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
// ---------- 文档检索 ----------
bool searchDoc(DocManagerWithIndex& mgr, const char* key, int alg, Filter f, SearchHistoryQueue& his) {
    printf("\n====== 搜索关键词 “%s” ======\n", key);
    if (*f.category) printf("  栏目: %s\n", f.category);
    if (*f.author)   printf("  作者: %s\n", f.author);
    if (*f.status)   printf("  状态: %s\n", f.status);
    if (*f.startDate) printf("  起始日期: %s\n", f.startDate);
    if (*f.endDate)  printf("  结束日期: %s\n", f.endDate);

    int idArr[MAX_SIZE], idNum = 0;
    if (alg == 3) {
        int num;
        int* ids = mgr.getIndex().search(key, num);
        if (ids) { idNum = num; for (int i = 0; i < num; i++) idArr[i] = ids[i]; }
    } else {
        idNum = mgr.getLength();
        for (int i = 0; i < idNum; i++) idArr[i] = mgr.getDoc(i)->id;
    }

    int findCnt = 0;
    for (int i = 0; i < idNum; i++) {
        Document* d = mgr.findById(idArr[i]);
        if (!d || !filterDoc(d, f)) continue;
        bool match = false;
        if (alg == 1) match = (BF(d->title, key) != -1 || BF(d->content, key) != -1);
        else if (alg == 2) match = (KMP(d->title, key) != -1 || KMP(d->content, key) != -1);
        else if (alg == 3) match = true;
        if (!match) continue;

        findCnt++;
        printDoc(d);
        if (strstr(d->content, key)) {
            printf("  [内容高亮] ");
            highlight(d->content, key);
        }
    }

    if (findCnt == 0) { puts("未找到任何符合条件的文档。"); return false; }
    printf("共找到 %d 篇文档。\n", findCnt);
    his.enq(key);
    return true;
}

// ---------- 算法效率对比（使用文档库真实数据） ----------
void compareAlgorithms(DocManagerWithIndex& mgr) {
    printf("\n====== BF vs KMP vs BST 效率对比测试 ======\n");
    char text[MAX_CONTENT * 2] = {0};
    int longestIdx = -1, maxLen = 0;
    for (int i = 0; i < mgr.getLength(); i++) {
        Document* d = mgr.getDoc(i);
        int len = strlen(d->content);
        if (len > maxLen) { maxLen = len; longestIdx = i; }
    }
    if (longestIdx != -1 && maxLen > 20) {
        strcpy(text, mgr.getDoc(longestIdx)->content);
    } else {
        // 若文档库为空或太短，使用内置测试文本
        strcpy(text, "数据结构是计算机存储、组织数据的方式。"
                     "数据结构是指相互之间存在一种或多种特定关系的数据元素的集合。"
                     "通常情况下，精心选择的数据结构可以带来更高的运行或者存储效率。"
                     "数据结构往往同高效的检索算法和索引技术有关。"
                     "KMP算法是一种改进的字符串匹配算法，由D.E.Knuth、J.H.Morris和V.R.Pratt同时发现。"
                     "BF算法是朴素的字符串匹配算法，时间复杂度较高。"
                     "在数据结构的实践中，我们经常需要处理字符串匹配问题。");
    }

    printf("测试文本长度: %d 字符\n", (int)strlen(text));
    const char* patterns[] = { "数据", "算法", "KMP", "字符串", "结构", "计算机", "匹配" };
    int patternCount = 7;

    printf("\n%-15s %-15s %-15s %-15s %-15s\n", "模式串", "BF耗时(us)", "KMP耗时(us)", "BST索引耗时(us)", "提速比(BF/KMP)");
    printf("----------------------------------------------------------------------------\n");

    for (int k = 0; k < patternCount; k++) {
        const char* p = patterns[k];
        if (strlen(p) > strlen(text)) continue;

        clock_t s, e;

        // BF
        s = clock(); BF(text, p); e = clock();
        double t1 = (double)(e - s) * 1000000.0 / CLOCKS_PER_SEC;

        // KMP
        s = clock(); KMP(text, p); e = clock();
        double t2 = (double)(e - s) * 1000000.0 / CLOCKS_PER_SEC;

        // BST 索引搜索
        int tmp;
        s = clock(); mgr.getIndex().search(p, tmp); e = clock();
        double t3 = (double)(e - s) * 1000000.0 / CLOCKS_PER_SEC;

        double ratio = (t2 > 0) ? (t1 / t2) : 0.0;

        printf("%-15s %-15.2f %-15.2f %-15.2f %-15.2f\n", p, t1, t2, t3, ratio);
    }
    printf("\n注：提速比 = BF耗时 / KMP耗时，>1 表示 KMP 更快。\n");
    printf("BST索引耗时仅包含搜索树的时间，不包含建索引时间。\n");
}

// ---------- 校园导航（图 + Dijkstra） ----------
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

// ---------- 主程序 ----------
int main() {
    DocManagerWithIndex docLib;
    docLib.loadFromFile();
    UndoStack undoOp;
    SearchHistoryQueue searchHis;
    CampusMap navMap;

    int nextId = 1;
    for (int i = 0; i < docLib.getLength(); i++)
        if (docLib.getDoc(i)->id >= nextId)
            nextId = docLib.getDoc(i)->id + 1;

    int op;
    while (1) {
        printf("\n╔══════════════════════════════════════════════════════════════════════╗\n");
        printf("║     简易搜索引擎 V5.0 （BST倒排索引 · 校园导航）                     ║\n");
        printf("╠══════════════════════════════════════════════════════════════════════╣\n");
        printf("║  1. 添加文档   2. 删除文档   3. 修改文档   4. 查看全部文档           ║\n");
        printf("║  5. 搜索文档   6. 撤销操作   7. 查看搜索历史   8. 保存并退出         ║\n");
        printf("║  9. 算法效率对比测试 (BF vs KMP vs BST)                              ║\n");
        printf("║ 10. 校园导航 - 添加点位  11. 校园导航 - 添加道路  12. 查询导航路径   ║\n");
        printf("╚══════════════════════════════════════════════════════════════════════╝\n");
        printf("请选择: ");
        scanf("%d", &op);
        getchar();

        if (op == 8) {
            docLib.saveToFile();
            printf("? 文档已保存，再见！\n");
            break;
        }

        // ----- 文档管理 -----
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
                undoOp.push({OP_ADD, d});
                printf("? 添加成功！文档ID: %d\n", nextId);
                nextId++;
            } else {
                printf("? 添加失败：文档库已满\n");
            }
        }
        else if (op == 2) {
            int id;
            printf("请输入要删除的文档ID: ");
            scanf("%d", &id);
            getchar();
            Document* d = docLib.findById(id);
            if (d) {
                undoOp.push({OP_DELETE, *d});
                docLib.deleteById(id);
                printf("? 删除成功（可撤销）\n");
            } else {
                printf("? 未找到ID为%d的文档\n", id);
            }
        }
        else if (op == 3) {
            int id;
            printf("请输入要修改的文档ID: ");
            scanf("%d", &id);
            getchar();
            Document* d = docLib.findById(id);
            if (!d) { printf("? 未找到ID为%d的文档\n", id); continue; }

            printf("当前文档信息：\n");
            printDoc(d);
            undoOp.push({OP_UPDATE, *d});

            char t[MAX_TITLE]="", c[MAX_CONTENT]="", ca[MAX_CATEGORY]="", a[MAX_AUTHOR]="", s[20]="", dt[20]="";
            printf("\n(直接回车表示不修改)\n");
            printf("新标题 [%s]: ", d->title); fgets(t, MAX_TITLE, stdin); t[strcspn(t, "\n")] = 0;
            printf("新内容 [%s...]: ", d->content); fgets(c, MAX_CONTENT, stdin); c[strcspn(c, "\n")] = 0;
            printf("新栏目 [%s]: ", d->category); fgets(ca, MAX_CATEGORY, stdin); ca[strcspn(ca, "\n")] = 0;
            printf("新作者 [%s]: ", d->author); fgets(a, MAX_AUTHOR, stdin); a[strcspn(a, "\n")] = 0;
            printf("新状态 [%s]: ", d->status); fgets(s, 20, stdin); s[strcspn(s, "\n")] = 0;
            printf("新日期 [%s]: ", d->publishDate); fgets(dt, 20, stdin); dt[strcspn(dt, "\n")] = 0;

            docLib.updateById(id, t, c, ca, a, s, dt);
            printf("? 修改成功（可撤销）\n");
        }
        else if (op == 4) {
            printf("\n--- 全部文档列表 (共%d篇) ---\n", docLib.getLength());
            if (docLib.getLength() == 0) printf("暂无文档\n");
            else for (int i = 0; i < docLib.getLength(); i++) printDoc(docLib.getDoc(i));
        }
        else if (op == 5) {
            printf("请输入搜索关键词: ");
            char key[MAX_CONTENT];
            fgets(key, MAX_CONTENT, stdin); key[strcspn(key, "\n")] = 0;
            if (strlen(key) == 0) { printf("关键词不能为空。\n"); continue; }

            int alg;
            printf("\n请选择匹配算法:\n");
            printf("  1. BF (Brute-Force) 朴素匹配\n");
            printf("  2. KMP (Knuth-Morris-Pratt) 快速匹配\n");
            printf("  3. BST 索引搜索 (V4.0 新功能)\n");
            printf("请选择 (1/2/3): ");
            scanf("%d", &alg); getchar();
            if (alg < 1 || alg > 3) { printf("无效选择，默认使用 KMP。\n"); alg = 2; }

            char yn;
            printf("\n是否启用多维度筛选? (y/n): ");
            scanf("%c", &yn); getchar();
            Filter f = {"", "", "", "", ""};
            if (yn == 'y' || yn == 'Y') {
                printf("  [筛选条件 - 直接回车表示不限]\n");
                printf("  栏目: "); fgets(f.category, MAX_CATEGORY, stdin); f.category[strcspn(f.category, "\n")] = 0;
                printf("  作者: "); fgets(f.author, MAX_AUTHOR, stdin); f.author[strcspn(f.author, "\n")] = 0;
                printf("  状态: "); fgets(f.status, 20, stdin); f.status[strcspn(f.status, "\n")] = 0;
                printf("  起始日期(YYYY-MM-DD): "); fgets(f.startDate, 20, stdin); f.startDate[strcspn(f.startDate, "\n")] = 0;
                printf("  结束日期(YYYY-MM-DD): "); fgets(f.endDate, 20, stdin); f.endDate[strcspn(f.endDate, "\n")] = 0;
            }

            searchDoc(docLib, key, alg, f, searchHis);
        }
        else if (op == 6) {
            Action ac;
            if (!undoOp.pop(ac)) { printf("没有可撤销的操作。\n"); continue; }
            if (ac.type == OP_ADD) docLib.deleteById(ac.doc.id);
            else if (ac.type == OP_DELETE) docLib.addDoc(ac.doc);
            else docLib.updateById(ac.doc.id, ac.doc.title, ac.doc.content,
                                   ac.doc.category, ac.doc.author,
                                   ac.doc.status, ac.doc.publishDate);
            printf("? 已撤销操作\n");
        }
        else if (op == 7) searchHis.show();
        else if (op == 9) compareAlgorithms(docLib);

        // ----- 校园导航 -----
        else if (op == 10) {
            int id; char n[32];
            printf("请输入点位ID和名称（例如: 101 图书馆）: ");
            scanf("%d %s", &id, n); getchar();
            if (navMap.addPoint(id, n)) printf("? 点位添加成功\n");
            else printf("? 添加失败（ID重复或点位已满）\n");
        }
        else if (op == 11) {
            int a, b, w;
            printf("请输入两个点位ID和距离（例如: 101 102 200）: ");
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
        else {
            printf("? 无效选择，请重新输入\n");
        }
    }
    return 0;
}
