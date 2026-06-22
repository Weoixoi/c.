#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <cctype>
#include <queue>
#include <algorithm>

using namespace std;

#define MAX_SIZE 100
#define MAX_TITLE 100
#define MAX_CONTENT 500
#define MAX_CATEGORY 20
#define MAX_AUTHOR 50
#define MAX_KEYWORD 50
#define MAX_DOCS_PER_KEY 50
#define DATA_FILE "documents.txt"
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

// ---------- 顺序表管理的文档库 ----------
class DocManager {
protected:
    Document data[MAX_SIZE];
    int length;
public:
    DocManager() { length = 0; }
    int getLength() { return length; }
    Document* getDoc(int idx) { return (idx >= 0 && idx < length) ? &data[idx] : nullptr; }

    int findIndexById(int id) {
        for (int i = 0; i < length; i++)
            if (data[i].id == id) return i;
        return -1;
    }

    bool addDoc(const Document& doc) {
        if (length >= MAX_SIZE) return false;
        data[length++] = doc;
        return true;
    }

    bool deleteById(int id) {
        int pos = findIndexById(id);
        if (pos == -1) return false;
        for (int i = pos; i < length - 1; i++)
            data[i] = data[i + 1];
        length--;
        return true;
    }

    bool updateById(int id, const char* t, const char* c, const char* ca,
                    const char* a, const char* s, const char* d) {
        int pos = findIndexById(id);
        if (pos == -1) return false;
        if (t && *t) strcpy(data[pos].title, t);
        if (c && *c) strcpy(data[pos].content, c);
        if (ca && *ca) strcpy(data[pos].category, ca);
        if (a && *a) strcpy(data[pos].author, a);
        if (s && *s) strcpy(data[pos].status, s);
        if (d && *d) strcpy(data[pos].publishDate, d);
        return true;
    }

    Document* findById(int id) {
        int pos = findIndexById(id);
        return (pos == -1) ? nullptr : &data[pos];
    }

    void saveToFile() {
        FILE* fp = fopen(DATA_FILE, "w");
        if (!fp) return;
        fprintf(fp, "%d\n", length);
        for (int i = 0; i < length; i++) {
            fprintf(fp, "%d\n%s\n%s\n%s\n%s\n%s\n%s\n",
                    data[i].id, data[i].title, data[i].content, data[i].category,
                    data[i].author, data[i].status, data[i].publishDate);
        }
        fclose(fp);
    }

    void loadFromFile() {
        FILE* fp = fopen(DATA_FILE, "r");
        if (!fp) return;
        int n;
        fscanf(fp, "%d\n", &n);
        Document tmp;
        for (int i = 0; i < n && i < MAX_SIZE; i++) {
            fscanf(fp, "%d\n", &tmp.id);
            fgets(tmp.title, MAX_TITLE, fp);   tmp.title[strcspn(tmp.title, "\n")] = 0;
            fgets(tmp.content, MAX_CONTENT, fp); tmp.content[strcspn(tmp.content, "\n")] = 0;
            fgets(tmp.category, MAX_CATEGORY, fp); tmp.category[strcspn(tmp.category, "\n")] = 0;
            fgets(tmp.author, MAX_AUTHOR, fp);  tmp.author[strcspn(tmp.author, "\n")] = 0;
            fgets(tmp.status, 20, fp);          tmp.status[strcspn(tmp.status, "\n")] = 0;
            fgets(tmp.publishDate, 20, fp);     tmp.publishDate[strcspn(tmp.publishDate, "\n")] = 0;
            addDoc(tmp);
        }
        fclose(fp);
    }
};

// ---------- 撤销栈 ----------
enum OpType { OP_ADD, OP_DELETE, OP_UPDATE };
struct Action { OpType type; Document doc; };
class UndoStack {
    static const int MAX_UNDO = 20;
    Action arr[MAX_UNDO];
    int top;
public:
    UndoStack() : top(0) {}
    bool push(Action ac) { if (top >= MAX_UNDO) return false; arr[top++] = ac; return true; }
    bool pop(Action& out) { if (top == 0) return false; out = arr[--top]; return true; }
    bool empty() { return top == 0; }
};
// ---------- 搜索历史队列 ----------
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

// ---------- BST 倒排索引 ----------
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
class BSTIndex {
    BSTNode* root;
    void ins(BSTNode*& p, const char* k, int id) {
        if (!p) { p = new BSTNode(k, id); return; }
        int cmp = strcmp(k, p->kw);
        if (cmp == 0) {
            for (int i = 0; i < p->cnt; i++) if (p->docId[i] == id) return;
            if (p->cnt < MAX_DOCS_PER_KEY) p->docId[p->cnt++] = id;
        }
        else if (cmp < 0) ins(p->l, k, id);
        else ins(p->r, k, id);
    }
    void del(BSTNode*& p, const char* k) {
        if (!p) return;
        int cmp = strcmp(k, p->kw);
        if (cmp < 0) del(p->l, k);
        else if (cmp > 0) del(p->r, k);
        else {
            BSTNode* t = p;
            if (!p->l) p = p->r;
            else if (!p->r) p = p->l;
            else {
                BSTNode* mi = p->r;
                while (mi->l) mi = mi->l;
                strcpy(p->kw, mi->kw);
                memcpy(p->docId, mi->docId, sizeof(p->docId));
                p->cnt = mi->cnt;
                del(p->r, mi->kw);
            }
            delete t;
        }
    }
    void clear(BSTNode* p) { if (!p) return; clear(p->l); clear(p->r); delete p; }
    int* find(BSTNode* p, const char* k, int& num) {
        if (!p) { num = 0; return nullptr; }
        int cmp = strcmp(k, p->kw);
        if (cmp == 0) { num = p->cnt; return p->docId; }
        return (cmp < 0) ? find(p->l, k, num) : find(p->r, k, num);
    }
public:
    BSTIndex() : root(nullptr) {}
    ~BSTIndex() { clear(root); }
    void insert(const char* k, int id) { ins(root, k, id); }
    void removeKey(const char* k) { del(root, k); }
    int* search(const char* k, int& num) { return find(root, k, num); }
    void reset() { clear(root); root = nullptr; }
};

// ---------- 辅助：字符串小写、分词 ----------
void toLower(char* s) { for (int i = 0; s[i]; i++) s[i] = tolower(s[i]); }
void splitWord(const char* src, char buf[][MAX_KEYWORD], int& num) {
    num = 0;
    char tmp[MAX_CONTENT];
    strcpy(tmp, src);
    char* p = strtok(tmp, " .,!?;:\n\t");
    while (p && num < MAX_DOCS_PER_KEY * 2) {
        if (strlen(p) > 1) {
            strcpy(buf[num], p);
            toLower(buf[num]);
            num++;
        }
        p = strtok(nullptr, " .,!?;:\n\t");
    }
}

// ---------- 带索引的文档管理器 ----------
class DocManagerWithIndex : public DocManager {
    BSTIndex idx;
    void rebuild() {
        idx.reset();
        for (int i = 0; i < length; i++) {
            Document* d = getDoc(i);
            char word[MAX_DOCS_PER_KEY * 2][MAX_KEYWORD];
            int wCnt;
            char all[MAX_CONTENT * 2];
            sprintf(all, "%s %s", d->title, d->content);
            splitWord(all, word, wCnt);
            for (int j = 0; j < wCnt; j++) idx.insert(word[j], d->id);
        }
    }
public:
    void loadFromFile() { DocManager::loadFromFile(); rebuild(); }
    bool addDoc(const Document& d) {
        bool ok = DocManager::addDoc(d);
        if (ok) {
            char word[MAX_DOCS_PER_KEY * 2][MAX_KEYWORD];
            int wCnt;
            char all[MAX_CONTENT * 2];
            sprintf(all, "%s %s", d.title, d.content);
            splitWord(all, word, wCnt);
            for (int j = 0; j < wCnt; j++) idx.insert(word[j], d.id);
        }
        return ok;
    }
    bool deleteById(int id) {
        bool ok = DocManager::deleteById(id);
        if (ok) rebuild();
        return ok;
    }
    bool updateById(int id, const char* t, const char* c, const char* ca,
                    const char* a, const char* s, const char* d) {
        bool ok = DocManager::updateById(id, t, c, ca, a, s, d);
        if (ok) rebuild();
        return ok;
    }
    BSTIndex& getIndex() { return idx; }
};

// ---------- BF / KMP 字符串匹配 ----------
int BF(const char* text, const char* pat) {
    int n = strlen(text), m = strlen(pat);
    for (int i = 0; i <= n - m; i++) {
        int j;
        for (j = 0; j < m; j++) if (text[i + j] != pat[j]) break;
        if (j == m) return i;
    }
    return -1;
}
void getNext(const char* pat, int* nxt) {
    int m = strlen(pat), i = 0, j = -1;
    nxt[0] = -1;
    while (i < m - 1) {
        if (j == -1 || pat[i] == pat[j]) nxt[++i] = ++j;
        else j = nxt[j];
    }
}
int KMP(const char* text, const char* pat) {
    int n = strlen(text), m = strlen(pat);
    int* nxt = new int[m];
    getNext(pat, nxt);
    int i = 0, j = 0;
    while (i < n && j < m) {
        if (j == -1 || text[i] == pat[j]) { i++; j++; }
        else j = nxt[j];
    }
    delete[] nxt;
    return (j == m) ? i - j : -1;
}

// ---------- 筛选、高亮、打印文档 ----------
bool filterDoc(Document* d, Filter f) {
    if (*f.category && strcmp(d->category, f.category)) return false;
    if (*f.author && strcmp(d->author, f.author)) return false;
    if (*f.status && strcmp(d->status, f.status)) return false;
    if (*f.startDate && strcmp(d->publishDate, f.startDate) < 0) return false;
    if (*f.endDate && strcmp(d->publishDate, f.endDate) > 0) return false;
    return true;
}
void highlight(const char* txt, const char* key) {
    const char* p = strstr(txt, key);
    if (!p) { puts(txt); return; }
    int pos = p - txt;
    int st = (pos > 40) ? pos - 40 : 0;
    char pre[100], suf[100];
    strncpy(pre, txt + st, pos - st); pre[pos - st] = 0;
    int ed = pos + strlen(key);
    int slen = strlen(txt) - ed;
    slen = (slen > 40) ? 40 : slen;
    strncpy(suf, txt + ed, slen); suf[slen] = 0;
    printf("%s【%s】%s\n", pre, key, suf);
}
void printDoc(Document* d) {
    printf("\n┌────────────────────────────────────────────────────────┐\n");
    printf("│ ID: %d\n", d->id);
    printf("│ 标题: %s\n", d->title);
    printf("│ 栏目: %s | 作者: %s | 状态: %s | 日期: %s\n",
           d->category, d->author, d->status, d->publishDate);
    char sum[100];
    strncpy(sum, d->content, 80); sum[80] = 0;
    printf("│ 摘要: %s%s\n", sum, strlen(d->content) > 80 ? "..." : "");
    printf("└────────────────────────────────────────────────────────┘\n");
}
