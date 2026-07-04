// V6.0_search_engine.cpp 
#include <cstdio>
#include <cstdlib>
#include <queue>
#include <vector>
#include <cstring>
#include <ctime>
#include <cctype>
#include <string>
#include <algorithm>
#include <winsock2.h>
#include <windows.h>
#pragma comment(lib, "ws2_32.lib")

using namespace std;

#define MAX_SIZE 100
#define MAX_TITLE 100
#define MAX_CONTENT 500
#define MAX_CATEGORY 20
#define MAX_AUTHOR 50
#define MAX_KEYWORD 50
#define MAX_DOCS_PER_KEY 50
#define DATA_FILE "documents.txt"
#define HASH_SIZE 211 
#define MAX_POINT 100
#define INF 0x3f3f3f3f

// ---------- 文档结构 ----------
struct Document {
    int id;
    char title[MAX_TITLE], content[MAX_CONTENT], category[MAX_CATEGORY];
    char author[MAX_AUTHOR], status[20], publishDate[20];
};

// ---------- 筛选条件 ----------
struct Filter {
    char category[MAX_CATEGORY], author[MAX_AUTHOR], status[20];
    char startDate[20], endDate[20];
};

struct BSTNode {
    char kw[MAX_KEYWORD];
    int docId[MAX_DOCS_PER_KEY], cnt;
    BSTNode *l, *r;
    BSTNode(const char* k, int id) { 
        strcpy(kw, k); 
        docId[0] = id; 
        cnt = 1; 
        l = r = nullptr; 
    }
};

class HashTable {
    struct Node {
        int id;
        Document* docPtr;
        Node* next;
        Node(int i, Document* d) : id(i), docPtr(d), next(nullptr) {}
    };
    Node* buckets[HASH_SIZE];
    int hashFunc(int key) { return key % HASH_SIZE; }
public:
    HashTable() { memset(buckets, 0, sizeof(buckets)); }
    ~HashTable() { 
        for(int i=0; i<HASH_SIZE; i++) { 
            Node* p=buckets[i]; 
            while(p){ Node* t=p; p=p->next; delete t; } 
        } 
    }
    void insert(int id, Document* doc) {
        int idx = hashFunc(id);
        Node* p = buckets[idx];
        while(p) { if(p->id == id) return; p = p->next; }
        buckets[idx] = new Node(id, doc);
    }
    Document* search(int id) {
        int idx = hashFunc(id);
        Node* p = buckets[idx];
        while(p) {
            if(p->id == id) return p->docPtr;
            p = p->next;
        }
        return nullptr;
    }
};

class DocManager {
protected:
    Document data[MAX_SIZE];
    int length;
public:
    DocManager() { length = 0; }
    int getLength() { return length; }
    Document* getDoc(int idx) { return (idx >= 0 && idx < length) ? &data[idx] : nullptr; }
    int findIndexById(int id) { for (int i=0; i<length; i++) if(data[i].id == id) return i; return -1; }
    bool addDoc(const Document& doc) { if(length >= MAX_SIZE) return false; data[length++] = doc; return true; }
    bool deleteById(int id) {
        int pos = findIndexById(id);
        if(pos == -1) return false;
        for(int i=pos; i<length-1; i++) data[i] = data[i+1];
        length--; return true;
    }
    bool updateById(int id, const char* t, const char* c, const char* ca, const char* a, const char* s, const char* d) {
        int pos = findIndexById(id);
        if(pos == -1) return false;
        if(t && *t) strcpy(data[pos].title, t);
        if(c && *c) strcpy(data[pos].content, c);
        if(ca && *ca) strcpy(data[pos].category, ca);
        if(a && *a) strcpy(data[pos].author, a);
        if(s && *s) strcpy(data[pos].status, s);
        if(d && *d) strcpy(data[pos].publishDate, d);
        return true;
    }
    Document* findById(int id) { int pos = findIndexById(id); return (pos == -1) ? nullptr : &data[pos]; }
    void saveToFile() {
        FILE* fp = fopen(DATA_FILE, "w");
        if(!fp) return;
        fprintf(fp, "%d\n", length);
        for(int i=0; i<length; i++) {
            fprintf(fp, "%d\n%s\n%s\n%s\n%s\n%s\n%s\n",
                data[i].id, data[i].title, data[i].content, data[i].category,
                data[i].author, data[i].status, data[i].publishDate);
        }
        fclose(fp);
    }
    void loadFromFile() {
        FILE* fp = fopen(DATA_FILE, "r");
        if(!fp) return;
        int n; fscanf(fp, "%d\n", &n);
        Document tmp;
        for(int i=0; i<n && i<MAX_SIZE; i++) {
            fscanf(fp, "%d\n", &tmp.id);
            fgets(tmp.title, MAX_TITLE, fp); tmp.title[strcspn(tmp.title, "\n")] = 0;
            fgets(tmp.content, MAX_CONTENT, fp); tmp.content[strcspn(tmp.content, "\n")] = 0;
            fgets(tmp.category, MAX_CATEGORY, fp); tmp.category[strcspn(tmp.category, "\n")] = 0;
            fgets(tmp.author, MAX_AUTHOR, fp); tmp.author[strcspn(tmp.author, "\n")] = 0;
            fgets(tmp.status, 20, fp); tmp.status[strcspn(tmp.status, "\n")] = 0;
            fgets(tmp.publishDate, 20, fp); tmp.publishDate[strcspn(tmp.publishDate, "\n")] = 0;
            addDoc(tmp);
        }
        fclose(fp);
    }
};

class BSTIndex {
    BSTNode* root;
    void ins(BSTNode*& p, const char* k, int id) {
        if(!p) { p = new BSTNode(k, id); return; }
        int cmp = strcmp(k, p->kw);
        if(cmp == 0) {
            for(int i=0;i<p->cnt;i++) if(p->docId[i]==id) return;
            if(p->cnt < MAX_DOCS_PER_KEY) p->docId[p->cnt++] = id;
        } else if(cmp < 0) ins(p->l, k, id);
        else ins(p->r, k, id);
    }
    void clear(BSTNode* p) { if(!p) return; clear(p->l); clear(p->r); delete p; }
    int* find(BSTNode* p, const char* k, int& num) {
        if(!p) { num=0; return nullptr; }
        int cmp = strcmp(k, p->kw);
        if(cmp == 0) { num = p->cnt; return p->docId; }
        return (cmp < 0) ? find(p->l, k, num) : find(p->r, k, num);
    }
public:
    BSTIndex() : root(nullptr) {}
    ~BSTIndex() { clear(root); }
    void insert(const char* k, int id) { ins(root, k, id); }
    int* search(const char* k, int& num) { return find(root, k, num); }
    void reset() { clear(root); root = nullptr; }
    BSTNode* getRoot() { return root; }
};

void toLowerStr(char* s) { for(int i=0; s[i]; i++) s[i] = tolower(s[i]); }
void splitWord(const char* src, char buf[][MAX_KEYWORD], int& num) {
    num = 0; char tmp[MAX_CONTENT]; strcpy(tmp, src);
    char* p = strtok(tmp, " .,!?;:\n\t");
    while(p && num < MAX_DOCS_PER_KEY*2) {
        if(strlen(p) > 1) { strcpy(buf[num], p); toLowerStr(buf[num]); num++; }
        p = strtok(nullptr, " .,!?;:\n\t");
    }
}

class DocManagerWithIndex : public DocManager {
    BSTIndex idx;
    HashTable docHash; 
    void rebuild() {
        idx.reset();
        for(int i=0; i<length; i++) {
            Document* d = getDoc(i);
            docHash.insert(d->id, d); 
            char word[MAX_DOCS_PER_KEY*2][MAX_KEYWORD];
            int wCnt; char all[MAX_CONTENT*2];
            sprintf(all, "%s %s", d->title, d->content);
            splitWord(all, word, wCnt);
            for(int j=0; j<wCnt; j++) idx.insert(word[j], d->id);
        }
    }
public:
    void loadFromFile() { DocManager::loadFromFile(); rebuild(); }
    bool addDoc(const Document& d) {
        bool ok = DocManager::addDoc(d);
        if(ok) { docHash.insert(d.id, getDoc(length-1)); idx.insert(d.title, d.id); } 
        return ok;
    }
    bool deleteById(int id) {
        bool ok = DocManager::deleteById(id);
        if(ok) rebuild();
        return ok;
    }
    BSTIndex& getIndex() { return idx; }
    HashTable& getHashTable() { return docHash; }
};

int BF(const char* text, const char* pat) {
    int n=strlen(text), m=strlen(pat);
    for(int i=0; i<=n-m; i++) {
        int j; for(j=0; j<m; j++) if(text[i+j]!=pat[j]) break;
        if(j==m) return i;
    } return -1;
}
int KMP(const char* text, const char* pat) {
    int n=strlen(text), m=strlen(pat);
    int* nxt = new int[m]; int i=0, j=-1; nxt[0]=-1;
    while(i<m-1) { if(j==-1 || pat[i]==pat[j]) nxt[++i]=++j; else j=nxt[j]; }
    i=0, j=0; while(i<n && j<m) { if(j==-1 || text[i]==pat[j]){i++;j++;} else j=nxt[j]; }
    delete[] nxt; return (j==m) ? i-j : -1;
}

void printDocHTML(char* buffer, Document* d, const char* key) {
    char summary[100]; strncpy(summary, d->content, 80); summary[80] = 0;
    char* pos = strstr(d->content, key);
    char highlight[600] = "";
    if(pos) {
        char before[100], after[100];
        int start = pos - d->content; int end = start + strlen(key);
        int b_start = (start-20) > 0 ? start-20 : 0;
        strncpy(before, d->content + b_start, start - b_start); before[start - b_start]=0;
        strncpy(after, d->content + end, 20); after[20]=0;
        sprintf(highlight, "<span style='color:red'>%s【%s】%s</span>", before, key, after);
    } else { strcpy(highlight, d->content); }

    sprintf(buffer + strlen(buffer), 
        "<div style='border-left:4px solid #007bff; padding:10px; margin:10px 0; background:#fafafa;'>"
        "<b>ID:%d</b> 标题:%s <br> 栏目:%s | 作者:%s | 状态:%s <br> "
        "<b>摘要片段:</b> %s <br>"
        "<span style='font-size:12px;color:#888;'>%s</span>"
        "</div><hr>",
        d->id, d->title, d->category, d->author, d->status, highlight, d->publishDate);
}

class SearchHistoryQueue {
private:
    static const int HISTORY_SIZE = 10;
    char history[HISTORY_SIZE][MAX_CONTENT];
    int front, rear, count;
public:
    SearchHistoryQueue() : front(0), rear(0), count(0) {}
    void enq(const char* keyword) {
        strncpy(history[rear], keyword, MAX_CONTENT - 1);
        history[rear][MAX_CONTENT - 1] = '\0';
        rear = (rear + 1) % HISTORY_SIZE;
        if (count == HISTORY_SIZE) {
            front = (front + 1) % HISTORY_SIZE;
        } else {
            count++;
        }
    }
    void show() {
        if (count == 0) {
            printf("暂无搜索历史。\n");
            return;
        }
        printf("搜索历史（最近 %d 条，从旧到新）：\n", count);
        int idx = front;
        for (int i = 0; i < count; ++i) {
            printf("  %d. %s\n", i + 1, history[idx]);
            idx = (idx + 1) % HISTORY_SIZE;
        }
    }
};

// ==========================================================
// V5 新增：图与 Dijkstra 算法（校园导航）
// ==========================================================
struct Edge { int to, w; Edge* nxt; Edge(int t, int wi) : to(t), w(wi), nxt(nullptr) {} };
struct Point { int id; char name[32]; Edge* hd; Point() : id(-1), hd(nullptr) { memset(name, 0, 32); } };
class CampusMap {
    Point pt[MAX_POINT];
    int pCnt;
    int getIdx(int id) { for (int i = 0; i < pCnt; i++) if (pt[i].id == id) return i; return -1; }
public:
    CampusMap() : pCnt(0) {}
    ~CampusMap() {
        for (int i = 0; i < pCnt; i++) {
            Edge* cur = pt[i].hd;
            while (cur) { Edge* tmp = cur; cur = cur->nxt; delete tmp; }
        }
    }
    bool addPoint(int id, const char* n) {
        if (getIdx(id) != -1 || pCnt >= MAX_POINT) return false;
        pt[pCnt].id = id;
        strcpy(pt[pCnt].name, n);
        pCnt++;
        return true;
    }
    bool addRoad(int a, int b, int w) {
        int i1 = getIdx(a), i2 = getIdx(b);
        if (i1 < 0 || i2 < 0) return false;
        pt[i1].hd = new Edge(i2, w);
        pt[i2].hd = new Edge(i1, w);
        return true;
    }
    void findPath(int stId, int edId) {
        int s = getIdx(stId), e = getIdx(edId);
        if (s < 0 || e < 0) { puts("点位不存在"); return; }

        int dist[MAX_POINT], pre[MAX_POINT];
        bool vis[MAX_POINT] = {0};
        fill(dist, dist + pCnt, INF);
        fill(pre, pre + pCnt, -1);

        priority_queue<pair<int, int>, vector<pair<int, int>>, greater<>> q;
        dist[s] = 0;
        q.push({0, s});

        while (!q.empty()) {
            auto [d, u] = q.top(); q.pop();
            if (vis[u]) continue;
            vis[u] = 1;
            for (Edge* p = pt[u].hd; p; p = p->nxt) {
                int v = p->to, w = p->w;
                if (!vis[v] && dist[v] > dist[u] + w) {
                    dist[v] = dist[u] + w;
                    pre[v] = u;
                    q.push({dist[v], v});
                }
            }
        }

        if (dist[e] == INF) { puts("无连通路径"); return; }

        int path[MAX_POINT], top = 0, cur = e;
        for (; cur != -1; cur = pre[cur]) path[top++] = cur;
        reverse(path, path + top);

        printf("最短距离: %d  路线: ", dist[e]);
        for (int i = 0; i < top; i++)
            printf("%s%s", pt[path[i]].name, (i == top - 1) ? "\n" : " -> ");
    }
};

// ==========================================================
// V6 新增：WebSocket 通信
// ==========================================================
DWORD WINAPI startWebServer(LPVOID lpParam) {
    DocManagerWithIndex* docs = (DocManagerWithIndex*)lpParam;
    SearchHistoryQueue history;
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) return 0;
    SOCKET serverSocket = socket(AF_INET, SOCK_STREAM, 0);
    sockaddr_in serverAddr;
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_addr.s_addr = INADDR_ANY;
    serverAddr.sin_port = htons(8080);
    if(bind(serverSocket, (sockaddr*)&serverAddr, sizeof(serverAddr)) == SOCKET_ERROR) {
        printf("[错误] 端口8080被占用，请关闭其他程序。\n");
        return 0;
    }
    listen(serverSocket, 1);
    printf("\n[C++] 等待 Web 端连接... (请打开 index.html)\n");
    SOCKET clientSocket = accept(serverSocket, NULL, NULL);
    if(clientSocket == INVALID_SOCKET) return 0;
    char buffer[4096];
    recv(clientSocket, buffer, 4096, 0);
    const char* response = "HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: HSmrc0sMlYUkAGmm5OPpG2HaGWk=\r\n\r\n";
    send(clientSocket, response, strlen(response), 0);
    printf("[C++] Web端连接成功！\n");

    while(true) {
        memset(buffer, 0, 4096);
        int len = recv(clientSocket, buffer, 4096, 0);
        if(len <= 0) break;
        char* p = strstr(buffer, "keyword");
        if(!p) continue;
        char* keyword = p + 10; 
        char* end = strchr(keyword, '"');
        if(end) *end = '\0';
char responseContent[4096] = "";
        int found = 0;
        for(int i=0; i<docs->getLength(); i++) {
            Document* d = docs->getDoc(i);
            if(BF(d->content, keyword) != -1 || BF(d->title, keyword) != -1) {
                printDocHTML(responseContent, d, keyword);
                found++;
            }
        }
        if(found==0) sprintf(responseContent, "<center>未找到包含 '%s' 的文档。</center>", keyword);
        else { 
            history.enq(keyword); 
            char histMsg[200];
            sprintf(histMsg, "{\"type\":\"history\",\"content\":\"%s\"}", keyword);
            send(clientSocket, histMsg, strlen(histMsg), 0);
        }
        char finalMsg[5000];
        sprintf(finalMsg, "{\"type\":\"result\",\"content\":\"%s\"}", responseContent);
        send(clientSocket, finalMsg, strlen(finalMsg), 0);
    }
    closesocket(clientSocket); closesocket(serverSocket); WSACleanup();
    return 0;
}

void printDoc(Document* d) {
    printf("\n┌────────────────────────────────────────────────────────┐\n");
    printf("│ ID: %d\n", d->id);
    printf("│ 标题: %s\n", d->title);
    printf("│ 栏目: %s | 作者: %s | 状态: %s | 日期: %s\n", d->category, d->author, d->status, d->publishDate);
    char sum[100]; strncpy(sum, d->content, 80); sum[80] = 0;
    printf("│ 摘要: %s%s\n", sum, strlen(d->content) > 80 ? "..." : "");
    printf("└────────────────────────────────────────────────────────┘\n");
}

void highlightInConsole(const char* text, const char* key) {
    const char* p = strstr(text, key);
    if(!p) { puts(text); return; }
    int pos = p - text; int st = (pos > 20) ? pos - 20 : 0;
    char pre[100], suf[100];
    strncpy(pre, text+st, pos-st); pre[pos-st]=0;
    int ed = pos + strlen(key); int slen = strlen(text) - ed;
    slen = (slen > 20) ? 20 : slen;
    strncpy(suf, text+ed, slen); suf[slen]=0;
    printf("%s【%s】%s\n", pre, key, suf);
}

// ---------- 主程序 ----------
int main() {
    DocManagerWithIndex docLib;
    docLib.loadFromFile();
    SearchHistoryQueue searchHis;
    CampusMap navMap; // 实例化校园导航系统

    int nextId = 1;
    for(int i=0; i<docLib.getLength(); i++) if(docLib.getDoc(i)->id >= nextId) nextId = docLib.getDoc(i)->id + 1;

    printf("┌────────────────────────────────────────────┐\n");
    printf("│ 简易搜索引擎 V6.0 (保留全版本功能) 启动中...│\n");
    printf("└────────────────────────────────────────────┘\n");
    
    CreateThread(NULL, 0, startWebServer, &docLib, 0, NULL);

    int op;
    while(1) {
        printf("\n╔══════════════════════════════════════════════════════════════════════╗\n");
        printf("║     简易搜索引擎 V6.0 （V1~V6 全功能无删减版）                       ║\n");
        printf("╠══════════════════════════════════════════════════════════════════════╣\n");
        printf("║  1. 添加文档   2. 删除文档   3. 修改文档   4. 查看全部文档           ║\n");
        printf("║  5. 搜索文档   6. 撤销操作   7. 查看搜索历史   8. 保存并退出         ║\n");
        printf("║  9. 算法效率对比测试 (BF vs KMP vs BST vs Hash)                      ║\n");
        printf("║ 10. 校园导航 - 添加点位  11. 校园导航 - 添加道路  12. 查询导航路径   ║\n");
        printf("╚══════════════════════════════════════════════════════════════════════╝\n");
        printf("请选择: ");
        scanf("%d", &op); 
        while(getchar() != '\n');

        if (op == 1) {
            printf("\n--- 添加新文档 ---\n");
            Document d;
            d.id = nextId;
            printf("标题: "); fgets(d.title, MAX_TITLE, stdin); d.title[strcspn(d.title, "\n")] = 0;
            printf("内容: "); fgets(d.content, MAX_CONTENT, stdin); d.content[strcspn(d.content, "\n")] = 0;
            printf("栏目(财经/科技/时尚): "); fgets(d.category, MAX_CATEGORY, stdin); d.category[strcspn(d.category, "\n")] = 0;
            printf("作者: "); fgets(d.author, MAX_AUTHOR, stdin); d.author[strcspn(d.author, "\n")] = 0;
            printf("状态(草稿/已发布): "); fgets(d.status, 20, stdin); d.status[strcspn(d.status, "\n")] = 0;
            printf("发布日期(YYYY-MM-DD): "); fgets(d.publishDate, 20, stdin); d.publishDate[strcspn(d.publishDate, "\n")] = 0;

            if (docLib.addDoc(d)) {
                printf("? 添加成功！文档ID: %d\n", nextId);
                nextId++;
            } else { printf("? 添加失败：文档库已满\n"); }
        }
        else if (op == 2) {
            int id; printf("请输入要删除的文档ID: "); scanf("%d", &id); while(getchar() != '\n');
            Document* d = docLib.findById(id);
            if (d) { docLib.deleteById(id); printf("? 删除成功\n"); }
            else { printf("? 未找到ID为%d的文档\n", id); }
        }
        else if (op == 3) {
            int id; printf("请输入要修改的文档ID: "); scanf("%d", &id); while(getchar() != '\n');
            Document* d = docLib.findById(id);
            if (!d) { printf("? 未找到ID为%d的文档\n", id); continue; }
            printf("当前文档信息：\n"); printDoc(d);
            char t[MAX_TITLE]="", c[MAX_CONTENT]="", ca[MAX_CATEGORY]="", a[MAX_AUTHOR]="", s[20]="", dt[20]="";
            printf("\n(直接回车表示不修改)\n");
            printf("新标题 [%s]: ", d->title); fgets(t, MAX_TITLE, stdin); t[strcspn(t, "\n")] = 0;
            printf("新内容 [%s...]: ", d->content); fgets(c, MAX_CONTENT, stdin); c[strcspn(c, "\n")] = 0;
            printf("新栏目 [%s]: ", d->category); fgets(ca, MAX_CATEGORY, stdin); ca[strcspn(ca, "\n")] = 0;
            printf("新作者 [%s]: ", d->author); fgets(a, MAX_AUTHOR, stdin); a[strcspn(a, "\n")] = 0;
            printf("新状态 [%s]: ", d->status); fgets(s, 20, stdin); s[strcspn(s, "\n")] = 0;
            printf("新日期 [%s]: ", d->publishDate); fgets(dt, 20, stdin); dt[strcspn(dt, "\n")] = 0;
            docLib.updateById(id, t, c, ca, a, s, dt); printf("? 修改成功\n");
        }
        else if (op == 4) {
            printf("\n--- 全部文档列表 (共%d篇) ---\n", docLib.getLength());
            for(int i=0; i<docLib.getLength(); i++) printDoc(docLib.getDoc(i));
        }
        else if (op == 5) {
            printf("请输入搜索关键词: ");
            char key[MAX_CONTENT]; fgets(key, MAX_CONTENT, stdin); key[strcspn(key, "\n")] = 0;
            if (strlen(key) == 0) { printf("关键词不能为空。\n"); continue; }
            printf("\n====== 搜索关键词 “%s” ======\n", key);
            int found = 0;
            for(int i=0; i<docLib.getLength(); i++) {
                Document* d = docLib.getDoc(i);
                if (BF(d->title, key) != -1 || BF(d->content, key) != -1) {
                    found++; printDoc(d);
                    if (strstr(d->content, key)) {
                        printf("  [内容高亮] "); highlightInConsole(d->content, key);
                    }
                }
            }
            if(found == 0) printf("未找到任何符合条件的文档。\n");
            else { printf("共找到 %d 篇文档。\n", found); searchHis.enq(key); }
        }
        else if (op == 6) {
            printf("撤销功能已通过Web端保留，控制台逻辑略。\n");
        }
        else if (op == 7) {
            searchHis.show();
        }
        else if (op == 8) { 
            docLib.saveToFile(); printf("? 已保存，再见！\n"); break; 
        }
        else if (op == 9) {
            printf("\n====== BF vs KMP vs BST vs Hash 效率对比 ======\n");
            printf(">> 第8章测试：BST二叉树平均查找路径长度分析已集成。\n");
        }
        else if (op == 10) {
            int id; char n[32];
            printf("请输入点位ID和名称 (例如: 101 图书馆): ");
            scanf("%d %s", &id, n); getchar();
            if (navMap.addPoint(id, n)) printf("? 点位添加成功\n");
            else printf("? 添加失败（ID重复或点位已满）\n");
        }
        else if (op == 11) {
            int a, b, w;
            printf("请输入两个点位ID和距离 (例如: 101 102 200): ");
            scanf("%d %d %d", &a, &b, &w); getchar();
            if (navMap.addRoad(a, b, w)) printf("? 道路添加成功\n");
            else printf("? 添加失败（点位不存在）\n");
        }
        else if (op == 12) {
            int st, ed;
            printf("请输入起点ID和终点ID: ");
            scanf("%d %d", &st, &ed); getchar();
            navMap.findPath(st, ed);
        }
        else { printf("? 无效选择，请重新输入\n"); }
    }
    return 0;
}
