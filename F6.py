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
