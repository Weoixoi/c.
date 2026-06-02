// V2.0_search_engine.cpp
// 简易搜索引擎 V2.0 —— 加入栈（撤销）和队列（搜索历史）
// 编译：g++ -std=c++11 V2.0_search_engine.cpp -o V2
// 或使用 Dev-C++ 新建 C++ 文件编译运行

#include <cstdio>
#include <cstdlib>
#include <cstring>

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
=======

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

// ---------- 辅助函数：打印文档 ----------
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

// 显示包含关键词的段落（高亮）
void highlightKeyword(const char* text, const char* keyword) {
    const char* pos = strstr(text, keyword);
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

// 搜索文档并展示结果（返回是否找到）
bool searchDocs(DocManager& manager, const char* keyword, SearchHistoryQueue& history) {
    printf("\n====== 搜索关键词 “%s” ======\n", keyword);
    int foundCount = 0;
    for (int i = 0; i < manager.getLength(); ++i) {
        Document* doc = manager.getDoc(i);
        if (strstr(doc->title, keyword) || strstr(doc->content, keyword)) {
            foundCount++;
            printDoc(doc);
            // 展示包含关键词的摘要（在内容中高亮）
            if (strstr(doc->content, keyword)) {
                printf("  [内容高亮] ");
                highlightKeyword(doc->content, keyword);
            }
        }
    }
    if (foundCount == 0) {
        printf("未找到任何包含 “%s” 的文档。\n", keyword);
        return false;
    } else {
        printf("共找到 %d 篇文档。\n", foundCount);
        // 成功搜索则将关键词入队
        history.enqueue(keyword);
        return true;
    }
}
