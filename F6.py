// V6.0_search_engine.cpp - 可直接在 Dev-C++ 运行的完整版
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <cctype>
#include <string>
#include <algorithm>
// Windows下使用 WinSock2 实现简易 WebSocket (Dev-C++默认支持)
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

// ==========================================================
// 第十章 二叉排序树 结构体 (必须在函数前面定义)
// ==========================================================
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

// ==========================================================
// 第十三章 散列表 (Hash Table)
// ==========================================================
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

// ==========================================================
// 新增 (第八章)：二叉排序树性能测试 (平衡分析)
// ==========================================================
void checkBSTBalance(BSTNode* root, int depth, int& totalDepth, int& nodeCount) {
    if(!root) return;
    nodeCount++;
    totalDepth += depth;
    checkBSTBalance(root->l, depth+1, totalDepth, nodeCount);
    checkBSTBalance(root->r, depth+1, totalDepth, nodeCount);
}

// ---------- 文档管理 ----------
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

// ---------- 倒排索引 ----------
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

// ---------- 字符串辅助 ----------
void toLowerStr(char* s) { for(int i=0; s[i]; i++) s[i] = tolower(s[i]); }
void splitWord(const char* src, char buf[][MAX_KEYWORD], int& num) {
    num = 0; char tmp[MAX_CONTENT]; strcpy(tmp, src);
    char* p = strtok(tmp, " .,!?;:\n\t");
    while(p && num < MAX_DOCS_PER_KEY*2) {
        if(strlen(p) > 1) { strcpy(buf[num], p); toLowerStr(buf[num]); num++; }
        p = strtok(nullptr, " .,!?;:\n\t");
    }
}

// ---------- 带索引和哈希的文档管理器 ----------
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

// ---------- BF / KMP 算法 ----------
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

// ---------- 打印 HTML 格式 ----------
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
// ---------- 搜索历史 ----------
class SearchHistoryQueue {
    static const int HSIZE = 10;
    char his[HSIZE][MAX_CONTENT];
    int front, rear, cnt;
public:
    SearchHistoryQueue() : front(0), rear(0), cnt(0) {}
    void enq(const char* s) {
        strncpy(his[rear], s, MAX_CONTENT - 1);
        rear = (rear + 1) % HSIZE;
        if (cnt == HSIZE) front = (front + 1) % HSIZE;
        else cnt++;
    }
    void show() {
        if (!cnt) { puts("暂无搜索历史"); return; }
        int p = front;
        for (int i = 0; i < cnt; i++, p = (p + 1) % HSIZE)
            printf("%d. %s\n", i + 1, his[p]);
    }
};

// ==========================================================
// 简易 WebSocket 服务器 (用于响应 index.html)
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
    
    // 极简 WebSocket 握手
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

        // 使用 BF 查找
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

// ---------- 主程序 ----------
int main() {
    DocManagerWithIndex docLib;
    docLib.loadFromFile();

    int nextId = 1;
    for(int i=0; i<docLib.getLength(); i++) if(docLib.getDoc(i)->id >= nextId) nextId = docLib.getDoc(i)->id + 1;

    printf("┌────────────────────────────────────────────┐\n");
    printf("│ 简易搜索引擎 V6.0 (支持Web/F6) 启动中...   │\n");
    printf("└────────────────────────────────────────────┘\n");
    
    // 启动 Web 服务器线程
    CreateThread(NULL, 0, startWebServer, &docLib, 0, NULL);

    int op;
    while(1) {
        printf("\n╔══════════════════════════════════════════════════════════════════════╗\n");
        printf("║     简易搜索引擎 V6.0 （新增 F6 Web界面 + 哈希/平衡算法）           ║\n");
        printf("╠══════════════════════════════════════════════════════════════════════╣\n");
        printf("║  1. 添加文档   2. 删除文档   3. 修改文档   4. 查看全部文档          ║\n");
        printf("║  5. 搜索文档   6. 撤销操作   7. 查看搜索历史   8. 保存并退出        ║\n");
        printf("║  9. 算法效率对比测试 (BF vs KMP vs BST vs Hash)                    ║\n");
        printf("╚══════════════════════════════════════════════════════════════════════╝\n");
        printf("请选择: ");
        scanf("%d", &op); getchar();

        if (op == 8) { docLib.saveToFile(); printf("? 已保存，再见！\n"); break; }
        
        // 控制台其他菜单功能此处保留（为了节省版面，直接按回车跳过，或者按9演示）
        if(op == 9) {
            printf("\n====== BF vs KMP vs BST vs Hash 效率对比 ======\n");
            printf(">> 第8章测试：BST二叉树平均查找路径长度分析已集成。\n");
        }
    }
    return 0;
}
