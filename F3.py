#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>     // 用于计时

#define MAX_SIZE 100
#define MAX_TITLE 100
#define MAX_CONTENT 500
#define MAX_CATEGORY 20
#define MAX_AUTHOR 50
#define DATA_FILE "documents.txt"

// ---------- 文档结构体 ----------
struct Document {
    int id;
    char title[MAX_TITLE];
    char content[MAX_CONTENT];
    char category[MAX_CATEGORY];
    char author[MAX_AUTHOR];
    char status[20];
    char publishDate[20];
};

// ---------- 筛选条件结构体 ----------
struct Filter {
    char category[MAX_CATEGORY];   // 栏目
    char author[MAX_AUTHOR];       // 作者
    char status[20];               // 状态
    char startDate[20];            // 起始日期
    char endDate[20];              // 结束日期
};

// ---------- 顺序表管理的文档库 ----------
class DocManager {
private:
    Document data[MAX_SIZE];
    int length;
public:
    DocManager() { length = 0; }
    int getLength() const { return length; }
    Document* getDoc(int idx) { return (idx >= 0 && idx < length) ? &data[idx] : nullptr; }

    // 按ID查找，返回索引，未找到返回 -1
    int findIndexById(int id) const {
        for (int i = 0; i < length; ++i)
            if (data[i].id == id) return i;
        return -1;
    }

    // 尾部添加文档（不检查ID重复，直接添加）
    bool addDoc(const Document& doc) {
        if (length >= MAX_SIZE) return false;
        data[length] = doc;
        length++;
        return true;
    }

    // 按ID删除
    bool deleteById(int id) {
        int idx = findIndexById(id);
        if (idx == -1) return false;
        for (int i = idx; i < length - 1; ++i)
            data[i] = data[i + 1];
        length--;
        return true;
    }

    // 按ID修改
    bool updateById(int id, const char* newTitle, const char* newContent,
                    const char* newCategory, const char* newAuthor,
                    const char* newStatus, const char* newDate) {
        int idx = findIndexById(id);
        if (idx == -1) return false;
        if (newTitle && strlen(newTitle) > 0)    strcpy(data[idx].title, newTitle);
        if (newContent && strlen(newContent) > 0) strcpy(data[idx].content, newContent);
        if (newCategory && strlen(newCategory) > 0) strcpy(data[idx].category, newCategory);
        if (newAuthor && strlen(newAuthor) > 0)  strcpy(data[idx].author, newAuthor);
        if (newStatus && strlen(newStatus) > 0)  strcpy(data[idx].status, newStatus);
        if (newDate && strlen(newDate) > 0)      strcpy(data[idx].publishDate, newDate);
        return true;
    }

    // 按ID获取文档指针
    Document* findById(int id) {
        int idx = findIndexById(id);
        return (idx != -1) ? &data[idx] : nullptr;
    }

    // 保存到文件
    void saveToFile() const {
        FILE* fp = fopen(DATA_FILE, "w");
        if (!fp) return;
        fprintf(fp, "%d\n", length);
        for (int i = 0; i < length; ++i) {
            fprintf(fp, "%d\n", data[i].id);
            fprintf(fp, "%s\n", data[i].title);
            fprintf(fp, "%s\n", data[i].content);
            fprintf(fp, "%s\n", data[i].category);
            fprintf(fp, "%s\n", data[i].author);
            fprintf(fp, "%s\n", data[i].status);
            fprintf(fp, "%s\n", data[i].publishDate);
        }
        fclose(fp);
    }

    // 从文件加载
    void loadFromFile() {
        FILE* fp = fopen(DATA_FILE, "r");
        if (!fp) return;
        int n;
        fscanf(fp, "%d\n", &n);
        for (int i = 0; i < n && i < MAX_SIZE; ++i) {
            Document doc;
            fscanf(fp, "%d\n", &doc.id);
            fgets(doc.title, MAX_TITLE, fp);   doc.title[strcspn(doc.title, "\n")] = 0;
            fgets(doc.content, MAX_CONTENT, fp); doc.content[strcspn(doc.content, "\n")] = 0;
            fgets(doc.category, MAX_CATEGORY, fp); doc.category[strcspn(doc.category, "\n")] = 0;
            fgets(doc.author, MAX_AUTHOR, fp);  doc.author[strcspn(doc.author, "\n")] = 0;
            fgets(doc.status, 20, fp);          doc.status[strcspn(doc.status, "\n")] = 0;
            fgets(doc.publishDate, 20, fp);     doc.publishDate[strcspn(doc.publishDate, "\n")] = 0;
            addDoc(doc);
        }
        fclose(fp);
    }
};

// ---------- 操作类型枚举 ----------
enum OpType { OP_ADD, OP_DELETE, OP_UPDATE };

// 栈中存放的操作记录
struct Action {
    OpType type;
    Document doc;   // 保存的文档快照（添加/删除/修改前的原文档）
};

// ---------- 顺序栈（用于撤销） ----------
class UndoStack {
private:
    static const int MAX_UNDO = 20;
    Action actions[MAX_UNDO];
    int top;
public:
    UndoStack() : top(0) {}
    bool isEmpty() const { return top == 0; }
    bool isFull() const { return top == MAX_UNDO; }
    bool push(const Action& act) {
        if (isFull()) return false;
        actions[top++] = act;
        return true;
    }
    bool pop(Action& act) {
        if (isEmpty()) return false;
        act = actions[--top];
        return true;
    }
};

// ---------- 循环队列（搜索历史） ----------
class SearchHistoryQueue {
private:
    static const int HISTORY_SIZE = 10;
    char history[HISTORY_SIZE][MAX_CONTENT];  // 每个关键字最大长度同文档内容
    int front, rear, count;
public:
    SearchHistoryQueue() : front(0), rear(0), count(0) {}
    bool isEmpty() const { return count == 0; }
    bool isFull() const { return count == HISTORY_SIZE; }
    void enqueue(const char* keyword) {
        strncpy(history[rear], keyword, MAX_CONTENT - 1);
        history[rear][MAX_CONTENT - 1] = '\0';
        rear = (rear + 1) % HISTORY_SIZE;
        if (isFull()) {
            front = (front + 1) % HISTORY_SIZE; // 覆盖最早记录
        } else {
            count++;
        }
    }
    void display() const {
        if (isEmpty()) {
            printf("暂无搜索历史。\n");
            return;
        }
        printf("搜索历史（最近 %d 条，从旧到新）：\n", count);
        int idx = front;
        for (int i = 0; i < count; ++i) {
            printf("  %d. %s\n", i+1, history[idx]);
            idx = (idx + 1) % HISTORY_SIZE;
        }
    }
};
// ========== V3.0 新增：BF 与 KMP 字符串匹配算法 ==========

// BF (Brute-Force) 算法
// 返回 pattern 在 text 中首次出现的位置，未找到则返回 -1
int BF(const char* text, const char* pattern) {
    int n = strlen(text);
    int m = strlen(pattern);
    if (m == 0) return 0;
    for (int i = 0; i <= n - m; ++i) {
        int j;
        for (j = 0; j < m; ++j) {
            if (text[i + j] != pattern[j]) break;
        }
        if (j == m) return i;
    }
    return -1;
}

// KMP 算法：计算 next 数组
void getNext(const char* pattern, int* next) {
    int m = strlen(pattern);
    next[0] = -1;
    int i = 0, j = -1;
    while (i < m - 1) {
        if (j == -1 || pattern[i] == pattern[j]) {
            ++i;
            ++j;
            next[i] = j;
        } else {
            j = next[j];
        }
    }
}

// KMP 算法：返回 pattern 在 text 中首次出现的位置，未找到则返回 -1
int KMP(const char* text, const char* pattern) {
    int n = strlen(text);
    int m = strlen(pattern);
    if (m == 0) return 0;
    int* next = new int[m];
    getNext(pattern, next);
    int i = 0, j = 0;
    while (i < n && j < m) {
        if (j == -1 || text[i] == pattern[j]) {
            ++i;
            ++j;
        } else {
            j = next[j];
        }
    }
    delete[] next;
    if (j == m) return i - j;
    return -1;
}

// ========== V3.0 新增：多维度筛选函数 ==========
// 判断文档是否满足筛选条件
bool docMatchFilter(const Document* doc, const Filter& filter) {
    // 栏目筛选
    if (strlen(filter.category) > 0 && strcmp(doc->category, filter.category) != 0)
        return false;
    // 作者筛选
    if (strlen(filter.author) > 0 && strcmp(doc->author, filter.author) != 0)
        return false;
    // 状态筛选
    if (strlen(filter.status) > 0 && strcmp(doc->status, filter.status) != 0)
        return false;
    // 日期范围筛选（字符串直接比较，假设格式 YYYY-MM-DD）
    if (strlen(filter.startDate) > 0 && strcmp(doc->publishDate, filter.startDate) < 0)
        return false;
    if (strlen(filter.endDate) > 0 && strcmp(doc->publishDate, filter.endDate) > 0)
        return false;
    return true;
}

// ========== V3.0 辅助函数：显示包含关键词的段落（高亮） ==========
void highlightKeyword(const char* text, const char* keyword) {
    const char* pos = strstr(text, keyword);  // 这里用 strstr 定位，也可替换为 BF 或 KMP
    if (!pos) {
        printf("%s\n", text);
        return;
    }
    // 输出关键词前40个字符
    int start = pos - text;
    int begin = (start > 40) ? start - 40 : 0;
    char before[100] = {0};
    strncpy(before, text + begin, start - begin);
    before[start - begin] = '\0';
    printf("%s", before);
    // 高亮关键词
    printf("【%s】", keyword);
    // 输出关键词后40个字符
    int end = start + strlen(keyword);
    int afterLen = strlen(text) - end;
    if (afterLen > 40) afterLen = 40;
    char after[100] = {0};
    strncpy(after, text + end, afterLen);
    after[afterLen] = '\0';
    printf("%s\n", after);
}

// ========== V3.0 打印文档 ==========
void printDoc(const Document* doc) {
    printf("\n┌────────────────────────────────────────────────────────┐\n");
    printf("│ ID: %d\n", doc->id);
    printf("│ 标题: %s\n", doc->title);
    printf("│ 栏目: %s | 作者: %s | 状态: %s | 日期: %s\n",
           doc->category, doc->author, doc->status, doc->publishDate);
    char summary[100];
    strncpy(summary, doc->content, 80);
    summary[80] = '\0';
    printf("│ 摘要: %s%s\n", summary, strlen(doc->content) > 80 ? "..." : "");
    printf("└────────────────────────────────────────────────────────┘\n");
}

// ========== V3.0 搜索函数（支持算法选择和筛选） ==========
bool searchDocs(DocManager& manager, const char* keyword, int algoType,
                const Filter& filter, SearchHistoryQueue& history) {
    printf("\n====== 搜索关键词 “%s” ======\n", keyword);
    if (strlen(filter.category) > 0)  printf("  栏目: %s\n", filter.category);
    if (strlen(filter.author) > 0)    printf("  作者: %s\n", filter.author);
    if (strlen(filter.status) > 0)    printf("  状态: %s\n", filter.status);
    if (strlen(filter.startDate) > 0) printf("  起始日期: %s\n", filter.startDate);
    if (strlen(filter.endDate) > 0)   printf("  结束日期: %s\n", filter.endDate);

    int foundCount = 0;
    int (*matchFunc)(const char*, const char*) = NULL;
    if (algoType == 1)      matchFunc = BF;
    else if (algoType == 2) matchFunc = KMP;
    else                    matchFunc = NULL;  // 不应发生

    for (int i = 0; i < manager.getLength(); ++i) {
        Document* doc = manager.getDoc(i);
        // 先筛选
        if (!docMatchFilter(doc, filter)) continue;
        // 再匹配关键词
        int posTitle = matchFunc(doc->title, keyword);
        int posContent = matchFunc(doc->content, keyword);
        if (posTitle != -1 || posContent != -1) {
            foundCount++;
            printDoc(doc);
            if (posContent != -1) {
                printf("  [内容高亮] ");
                highlightKeyword(doc->content, keyword);
            }
        }
    }

    if (foundCount == 0) {
        printf("未找到任何符合条件的文档。\n");
        return false;
    } else {
        printf("共找到 %d 篇文档。\n", foundCount);
        history.enqueue(keyword);
        return true;
    }
}

// ========== V3.0 新增：BF 与 KMP 效率对比测试 ==========
void compareBFvsKMP(DocManager& manager) {
    printf("\n====== BF vs KMP 算法效率对比测试 ======\n");
    // 构造一个较长的文本（使用文档库中最长的文档内容，若没有则使用内置测试串）
    char text[MAX_CONTENT * 2] = {0};
    int longestIdx = -1;
    int maxLen = 0;
    for (int i = 0; i < manager.getLength(); ++i) {
        Document* doc = manager.getDoc(i);
        int len = strlen(doc->content);
        if (len > maxLen) {
            maxLen = len;
            longestIdx = i;
        }
    }
    if (longestIdx != -1 && maxLen > 20) {
        strcpy(text, manager.getDoc(longestIdx)->content);
    } else {
        // 若文档库为空或内容太短，使用内置测试文本
        strcpy(text, "数据结构是计算机存储、组织数据的方式。"
                     "数据结构是指相互之间存在一种或多种特定关系的数据元素的集合。"
                     "通常情况下，精心选择的数据结构可以带来更高的运行或者存储效率。"
                     "数据结构往往同高效的检索算法和索引技术有关。"
                     "KMP算法是一种改进的字符串匹配算法，由D.E.Knuth、J.H.Morris和V.R.Pratt同时发现。"
                     "BF算法是朴素的字符串匹配算法，时间复杂度较高。"
                     "在数据结构的实践中，我们经常需要处理字符串匹配问题。");
    }

    printf("测试文本长度: %d 字符\n", (int)strlen(text));
    // 准备几个测试模式串
    const char* patterns[] = { "数据", "算法", "KMP", "字符串", "结构", "计算机", "匹配" };
    int patternCount = 7;

    printf("\n%-15s %-15s %-15s %-15s\n", "模式串", "BF耗时(us)", "KMP耗时(us)", "提速比");
    printf("------------------------------------------------------------\n");

    for (int k = 0; k < patternCount; ++k) {
        const char* p = patterns[k];
        int m = strlen(p);
        // 跳过长度大于文本的模式串
        if (m > strlen(text)) continue;

        // BF 计时
        clock_t start = clock();
        int posBF = BF(text, p);
        clock_t end = clock();
        double timeBF = (double)(end - start) * 1000000.0 / CLOCKS_PER_SEC;

        // KMP 计时
        start = clock();
        int posKMP = KMP(text, p);
        end = clock();
        double timeKMP = (double)(end - start) * 1000000.0 / CLOCKS_PER_SEC;

        double ratio = (timeBF > 0) ? (timeBF / timeKMP) : 0.0;

        printf("%-15s %-15.2f %-15.2f %-15.2f\n", p, timeBF, timeKMP, ratio);
        // 验证匹配位置是否一致
        if (posBF != posKMP) {
            printf("  [警告] 匹配位置不一致! BF: %d, KMP: %d\n", posBF, posKMP);
        }
    }
    printf("\n注：提速比 = BF耗时 / KMP耗时，>1 表示 KMP 更快。\n");
    printf("当前测试基于单次匹配，实际应用中模式串越长、文本越长，KMP优势越明显。\n");
}
