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
// ---------- 主程序 ----------
int main() {
    DocManager docs;
    docs.loadFromFile();
    UndoStack undoStack;
    SearchHistoryQueue searchHistory;

    // 计算下一个可用ID
    int nextId = 1;
    for (int i = 0; i < docs.getLength(); ++i) {
        if (docs.getDoc(i)->id >= nextId)
            nextId = docs.getDoc(i)->id + 1;
    }

    while (true) {
        printf("\n╔════════════════════════════════════════════════════════════╗\n");
        printf("║     简易搜索引擎 V2.0 （栈·撤销 / 队列·历史）              ║\n");
        printf("╠════════════════════════════════════════════════════════════╣\n");
        printf("║  1.添加文档  2.删除文档  3.修改文档  4.查看全部文档        ║\n");
        printf("║  5.搜索文档  6.撤销操作  7.查看搜索历史  8.保存并退出      ║\n");
        printf("╚════════════════════════════════════════════════════════════╝\n");
        printf("请选择: ");

        int choice;
        scanf("%d", &choice);
        getchar(); // 吞掉换行

        if (choice == 1) {  // 添加文档
            printf("\n--- 添加新文档 ---\n");
            Document doc;
            doc.id = nextId;
            printf("标题: ");   fgets(doc.title, MAX_TITLE, stdin);   doc.title[strcspn(doc.title, "\n")] = 0;
            printf("内容: ");   fgets(doc.content, MAX_CONTENT, stdin); doc.content[strcspn(doc.content, "\n")] = 0;
            printf("栏目(财经/科技/时尚): "); fgets(doc.category, MAX_CATEGORY, stdin); doc.category[strcspn(doc.category, "\n")] = 0;
            printf("作者: ");   fgets(doc.author, MAX_AUTHOR, stdin);   doc.author[strcspn(doc.author, "\n")] = 0;
            printf("状态(草稿/已发布): "); fgets(doc.status, 20, stdin); doc.status[strcspn(doc.status, "\n")] = 0;
            printf("发布日期(YYYY-MM-DD): "); fgets(doc.publishDate, 20, stdin); doc.publishDate[strcspn(doc.publishDate, "\n")] = 0;

            if (docs.addDoc(doc)) {
                printf("? 添加成功！文档ID: %d\n", nextId);
                // 记录操作（用于撤销）
                Action act;
                act.type = OP_ADD;
                act.doc = doc;
                undoStack.push(act);
                nextId++;
            } else {
                printf("? 添加失败：文档库已满\n");
            }
        }
        else if (choice == 2) {  // 删除文档
            int id;
            printf("请输入要删除的文档ID: ");
            scanf("%d", &id);
            getchar();
            Document* target = docs.findById(id);
            if (target) {
                // 保存文档快照，记录操作
                Action act;
                act.type = OP_DELETE;
                act.doc = *target;  // 复制一份
                undoStack.push(act);
                docs.deleteById(id);
                printf("? 删除成功（可撤销）\n");
            } else {
                printf("? 未找到ID为%d的文档\n", id);
            }
        }
        else if (choice == 3) {  // 修改文档
            int id;
            printf("请输入要修改的文档ID: ");
            scanf("%d", &id);
            getchar();
            Document* doc = docs.findById(id);
            if (doc) {
                printf("当前文档信息：\n");
                printDoc(doc);
                // 保存修改前的快照
                Action act;
                act.type = OP_UPDATE;
                act.doc = *doc;
                undoStack.push(act);

                char newTitle[MAX_TITLE] = "";
                char newContent[MAX_CONTENT] = "";
                char newCategory[MAX_CATEGORY] = "";
                char newAuthor[MAX_AUTHOR] = "";
                char newStatus[20] = "";
                char newDate[20] = "";

                printf("\n(直接回车表示不修改)\n");
                printf("新标题 [%s]: ", doc->title);         fgets(newTitle, MAX_TITLE, stdin);       newTitle[strcspn(newTitle, "\n")] = 0;
                printf("新内容 [%s...]: ", doc->content);    fgets(newContent, MAX_CONTENT, stdin);  newContent[strcspn(newContent, "\n")] = 0;
                printf("新栏目 [%s]: ", doc->category);     fgets(newCategory, MAX_CATEGORY, stdin); newCategory[strcspn(newCategory, "\n")] = 0;
                printf("新作者 [%s]: ", doc->author);       fgets(newAuthor, MAX_AUTHOR, stdin);    newAuthor[strcspn(newAuthor, "\n")] = 0;
                printf("新状态 [%s]: ", doc->status);       fgets(newStatus, 20, stdin);            newStatus[strcspn(newStatus, "\n")] = 0;
                printf("新日期 [%s]: ", doc->publishDate);  fgets(newDate, 20, stdin);              newDate[strcspn(newDate, "\n")] = 0;

                docs.updateById(id, newTitle, newContent, newCategory, newAuthor, newStatus, newDate);
                printf("? 修改成功（可撤销）\n");
            } else {
                printf("? 未找到ID为%d的文档\n", id);
            }
        }
        else if (choice == 4) {  // 查看全部
            printf("\n--- 全部文档列表 (共%d篇) ---\n", docs.getLength());
            if (docs.getLength() == 0)
                printf("暂无文档\n");
            else
                for (int i = 0; i < docs.getLength(); ++i)
                    printDoc(docs.getDoc(i));
        }
        else if (choice == 5) {  // 搜索文档
            printf("请输入搜索关键词: ");
            char keyword[MAX_CONTENT];
            fgets(keyword, MAX_CONTENT, stdin);
            keyword[strcspn(keyword, "\n")] = 0;
            if (strlen(keyword) == 0) {
                printf("关键词不能为空。\n");
                continue;
            }
            searchDocs(docs, keyword, searchHistory);
        }
        else if (choice == 6) {  // 撤销操作
            Action act;
            if (!undoStack.pop(act)) {
                printf("没有可撤销的操作。\n");
                continue;
            }
            if (act.type == OP_ADD) {
                // 撤销添加 -> 删除该文档
                if (docs.deleteById(act.doc.id))
                    printf("? 已撤销添加（删除文档 ID=%d）\n", act.doc.id);
                else
                    printf("? 撤销失败：可能文档已被删除\n");
            }
            else if (act.type == OP_DELETE) {
                // 撤销删除 -> 重新添加文档
                if (docs.addDoc(act.doc))
                    printf("? 已撤销删除（恢复文档 ID=%d）\n", act.doc.id);
                else
                    printf("? 撤销失败：文档库已满\n");
            }
            else if (act.type == OP_UPDATE) {
                // 撤销修改 -> 用旧文档覆盖
                int idx = docs.findIndexById(act.doc.id);
                if (idx != -1) {
                    docs.updateById(act.doc.id, act.doc.title, act.doc.content,
                                    act.doc.category, act.doc.author,
                                    act.doc.status, act.doc.publishDate);
                    printf("? 已撤销修改（恢复文档 ID=%d）\n", act.doc.id);
                } else {
                    // 如果文档已被删除，则恢复它（添加旧文档）
                    docs.addDoc(act.doc);
                    printf("? 已撤销修改并恢复文档 ID=%d\n", act.doc.id);
                }
            }
        }
        else if (choice == 7) {  // 查看搜索历史
            searchHistory.display();
        }
        else if (choice == 8) {  // 保存并退出
            docs.saveToFile();
            printf("? 文档已保存，再见！\n");
            break;
        }
        else {
            printf("? 无效选择，请重新输入\n");
        }
    }
    return 0;
}
