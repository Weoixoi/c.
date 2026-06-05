// V4.0_search_engine.cpp
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <cctype>

#define MAX_SIZE 100
#define MAX_TITLE 100
#define MAX_CONTENT 500
#define MAX_CATEGORY 20
#define MAX_AUTHOR 50
#define MAX_KEYWORD 50
#define MAX_DOCS_PER_KEY 50
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
    char category[MAX_CATEGORY];
    char author[MAX_AUTHOR];
    char status[20];
    char startDate[20];
    char endDate[20];
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

    int findIndexById(int id) const {
        for (int i = 0; i < length; ++i)
            if (data[i].id == id) return i;
        return -1;
    }

    bool addDoc(const Document& doc) {
        if (length >= MAX_SIZE) return false;
        data[length] = doc;
        length++;
        return true;
    }

    bool deleteById(int id) {
        int idx = findIndexById(id);
        if (idx == -1) return false;
        for (int i = idx; i < length - 1; ++i)
            data[i] = data[i + 1];
        length--;
        return true;
    }

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

    Document* findById(int id) {
        int idx = findIndexById(id);
        return (idx != -1) ? &data[idx] : nullptr;
    }

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

struct Action {
    OpType type;
    Document doc;
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
    bool push(const Action& act) {
        if (top >= MAX_UNDO) return false;
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
    char history[HISTORY_SIZE][MAX_CONTENT];
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
            front = (front + 1) % HISTORY_SIZE;
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

// ========== V4.0 核心：BST 倒排索引 ==========
struct BSTNode {
    char keyword[MAX_KEYWORD];
    int docIds[MAX_DOCS_PER_KEY];
    int docCount;
    BSTNode *left, *right;

    BSTNode(const char* kw, int docId) {
        strncpy(keyword, kw, MAX_KEYWORD - 1);
        keyword[MAX_KEYWORD - 1] = '\0';
        docIds[0] = docId;
        docCount = 1;
        left = right = nullptr;
    }
};

class BSTIndex {
private:
    BSTNode* root;

    void insertNode(BSTNode*& node, const char* kw, int docId) {
        if (node == nullptr) {
            node = new BSTNode(kw, docId);
            return;
        }
        int cmp = strcmp(kw, node->keyword);
        if (cmp == 0) {
            // 如果词已存在，避免重复添加相同ID
            for (int i = 0; i < node->docCount; ++i) {
                if (node->docIds[i] == docId) return;
            }
            if (node->docCount < MAX_DOCS_PER_KEY) {
                node->docIds[node->docCount++] = docId;
            }
        } else if (cmp < 0) {
            insertNode(node->left, kw, docId);
        } else {
            insertNode(node->right, kw, docId);
        }
    }

    void deleteNode(BSTNode*& node, const char* kw) {
        if (node == nullptr) return;
        int cmp = strcmp(kw, node->keyword);
        if (cmp < 0) {
            deleteNode(node->left, kw);
        } else if (cmp > 0) {
            deleteNode(node->right, kw);
        } else {
            // 找到节点，在这里只是删除该关键词（索引）
            BSTNode* temp = node;
            if (node->left == nullptr) {
                node = node->right;
                delete temp;
            } else if (node->right == nullptr) {
                node = node->left;
                delete temp;
            } else {
                BSTNode* minNode = node->right;
                while (minNode->left != nullptr) minNode = minNode->left;
                strcpy(node->keyword, minNode->keyword);
                node->docCount = minNode->docCount;
                for (int i = 0; i < minNode->docCount; ++i)
                    node->docIds[i] = minNode->docIds[i];
                deleteNode(node->right, minNode->keyword);
            }
        }
    }

    void clearTree(BSTNode* node) {
        if (node == nullptr) return;
        clearTree(node->left);
        clearTree(node->right);
        delete node;
    }

    int* searchNode(BSTNode* node, const char* kw, int& count) const {
        if (node == nullptr) {
            count = 0;
            return nullptr;
        }
        int cmp = strcmp(kw, node->keyword);
        if (cmp == 0) {
            count = node->docCount;
            return node->docIds;
        } else if (cmp < 0) {
            return searchNode(node->left, kw, count);
        } else {
            return searchNode(node->right, kw, count);
        }
    }

    void inorderPrint(BSTNode* node) const {
        if (node == nullptr) return;
        inorderPrint(node->left);
        printf("  '%s' -> %d docs\n", node->keyword, node->docCount);
        inorderPrint(node->right);
    }

public:
    BSTIndex() : root(nullptr) {}
    ~BSTIndex() { clearTree(root); }

    void insert(const char* kw, int docId) {
        insertNode(root, kw, docId);
    }

    void removeKeyword(const char* kw) {
        deleteNode(root, kw);
    }

    int* search(const char* kw, int& count) const {
        return searchNode(root, kw, count);
    }

    void printAll() const {
        inorderPrint(root);
    }

    void clear() {
        clearTree(root);
        root = nullptr;
    }
// 辅助：对于文档删除，需要遍历整个树移除对应docId
    void removeDocIdFromAll(int docId) {
        // 简单实现：重新构建索引（如果文档数量不大，可以接受）
        // 这里为了简化，实际上可以再做一次全量重建，但为了效率，我们可以在调用删除时使用更复杂的方法。
        // 本版本使用强制重建策略：当删除文档时调用rebuildFromDocs()
        // 但这里不实现复杂的遍历删除逻辑，因为重建索引代码在外部
        // 所以我们这个函数可以留空，在DocManager里处理重建。
    }
};

// ---------- 分词辅助 ----------
void toLowerCase(char* str) {
    for (int i = 0; str[i]; ++i) {
        str[i] = tolower(str[i]);
    }
}

void extractKeywords(const char* text, char keywords[][MAX_KEYWORD], int& count) {
    count = 0;
    char buffer[MAX_CONTENT];
    strcpy(buffer, text);
    char* p = buffer;
    char* word = strtok(p, " .,!?;:\n\t"); // 简单分词
    while (word != nullptr && count < MAX_DOCS_PER_KEY * 2) { // 限制关键词数量防止溢出
        if (strlen(word) > 1) { // 忽略单字符词
            strcpy(keywords[count], word);
            toLowerCase(keywords[count]);
            count++;
        }
        word = strtok(nullptr, " .,!?;:\n\t");
    }
}

// ---------- V4.0 文档管理器扩展 ----------
class DocManagerWithIndex : public DocManager {
private:
    BSTIndex index;

    void rebuildIndex() {
        index.clear();
        for (int i = 0; i < getLength(); ++i) {
            Document* doc = getDoc(i);
            char words[MAX_DOCS_PER_KEY * 2][MAX_KEYWORD];
            int wordCount = 0;
            // 从标题和内容提取
            char temp[MAX_CONTENT * 2];
            strcpy(temp, doc->title);
            strcat(temp, " ");
            strcat(temp, doc->content);
            extractKeywords(temp, words, wordCount);
            for (int j = 0; j < wordCount; ++j) {
                index.insert(words[j], doc->id);
            }
        }
    }

public:
    DocManagerWithIndex() : DocManager() {}

    void loadFromFile() {
        DocManager::loadFromFile();
        rebuildIndex();
    }

    bool addDoc(const Document& doc) {
        bool success = DocManager::addDoc(doc);
        if (success) {
            // 增量更新索引
            char words[MAX_DOCS_PER_KEY * 2][MAX_KEYWORD];
            int wordCount = 0;
            char temp[MAX_CONTENT * 2];
            strcpy(temp, doc.title);
            strcat(temp, " ");
            strcat(temp, doc.content);
            extractKeywords(temp, words, wordCount);
            for (int j = 0; j < wordCount; ++j) {
                index.insert(words[j], doc.id);
            }
        }
        return success;
    }

    bool deleteById(int id) {
        Document* doc = findById(id);
        if (doc == nullptr) return false;
        // 删除索引中关联的docId
        // 简单方法：完全重建索引（适用于文档量不大的情况）
        bool success = DocManager::deleteById(id);
        if (success) {
            rebuildIndex();
        }
        return success;
    }

    bool updateById(int id, const char* newTitle, const char* newContent,
                    const char* newCategory, const char* newAuthor,
                    const char* newStatus, const char* newDate) {
        Document* doc = findById(id);
        if (doc == nullptr) return false;
        bool success = DocManager::updateById(id, newTitle, newContent, newCategory, newAuthor, newStatus, newDate);
        if (success) {
            // 重新索引该文档（简单重建）
            rebuildIndex();
        }
        return success;
    }

    BSTIndex& getIndex() { return index; }
};

// ========== V4.0 保留 V3.0 的 BF/KMP ==========
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

bool docMatchFilter(const Document* doc, const Filter& filter) {
    if (strlen(filter.category) > 0 && strcmp(doc->category, filter.category) != 0)
        return false;
    if (strlen(filter.author) > 0 && strcmp(doc->author, filter.author) != 0)
        return false;
    if (strlen(filter.status) > 0 && strcmp(doc->status, filter.status) != 0)
        return false;
    if (strlen(filter.startDate) > 0 && strcmp(doc->publishDate, filter.startDate) < 0)
        return false;
    if (strlen(filter.endDate) > 0 && strcmp(doc->publishDate, filter.endDate) > 0)
        return false;
    return true;
}

void highlightKeyword(const char* text, const char* keyword) {
    const char* pos = strstr(text, keyword);
    if (!pos) {
        printf("%s\n", text);
        return;
    }
    int start = pos - text;
    int begin = (start > 40) ? start - 40 : 0;
    char before[100] = {0};
    strncpy(before, text + begin, start - begin);
    before[start - begin] = '\0';
    printf("%s", before);
    printf("【%s】", keyword);
    int end = start + strlen(keyword);
    int afterLen = strlen(text) - end;
    if (afterLen > 40) afterLen = 40;
    char after[100] = {0};
    strncpy(after, text + end, afterLen);
    after[afterLen] = '\0';
    printf("%s\n", after);
}

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
// ========== V4.0 搜索函数（支持BST索引、BF、KMP） ==========
bool searchDocs(DocManagerWithIndex& manager, const char* keyword, int algoType,
                const Filter& filter, SearchHistoryQueue& history) {
    printf("\n====== 搜索关键词 “%s” ======\n", keyword);
    if (strlen(filter.category) > 0)  printf("  栏目: %s\n", filter.category);
    if (strlen(filter.author) > 0)    printf("  作者: %s\n", filter.author);
    if (strlen(filter.status) > 0)    printf("  状态: %s\n", filter.status);
    if (strlen(filter.startDate) > 0) printf("  起始日期: %s\n", filter.startDate);
    if (strlen(filter.endDate) > 0)   printf("  结束日期: %s\n", filter.endDate);

    int foundCount = 0;
    int docIds[MAX_SIZE];
    int docIdCount = 0;

    if (algoType == 3) {
        // BST 索引搜索
        int count = 0;
        int* ids = manager.getIndex().search(keyword, count);
        if (ids != nullptr && count > 0) {
            docIdCount = count;
            for (int i = 0; i < count; ++i) {
                docIds[i] = ids[i];
            }
        } else {
            docIdCount = 0;
        }
    } else {
        // 线性扫描（BF/KMP）
        docIdCount = 0;
        for (int i = 0; i < manager.getLength(); ++i) {
            docIds[docIdCount++] = manager.getDoc(i)->id;  // 全部候选
        }
    }

    // 打印结果（先筛选）
    for (int i = 0; i < docIdCount; ++i) {
        int id = docIds[i];
        Document* doc = manager.findById(id);
        if (doc == nullptr) continue;
        // 筛选
        if (!docMatchFilter(doc, filter)) continue;
        // 匹配检查
        bool match = false;
        if (algoType == 1) {
            if (BF(doc->title, keyword) != -1 || BF(doc->content, keyword) != -1) match = true;
        } else if (algoType == 2) {
            if (KMP(doc->title, keyword) != -1 || KMP(doc->content, keyword) != -1) match = true;
        } else if (algoType == 3) {
            // 索引已经过滤了关键词，所以直接匹配
            match = true;
        }
        if (!match) continue;

        foundCount++;
        printDoc(doc);
        if (strstr(doc->content, keyword)) {
            printf("  [内容高亮] ");
            highlightKeyword(doc->content, keyword);
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

// ========== V4.0 增强：BF vs KMP vs BST 效率对比 ==========
void compareAlgorithms(DocManagerWithIndex& manager) {
    printf("\n====== BF vs KMP vs BST 效率对比测试 ======\n");
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
        strcpy(text,"数据结构是计算机存储、组织数据的方式。"
		                     "数据结构是指相互之间存在一种或多种特定关系的数据元素的集合。"
		                     "通常情况下，精心选择的数据结构可以带来更高的运行或者存储效率。"
		                     "数据结构往往同高效的检索算法和索引技术有关。"
		                     "KMP算法是一种改进的字符串匹配算法，由D.E.Knuth、J.H.Morris和V.R.Pratt同时发现。"
		                     "BF算法是朴素的字符串匹配算法，时间复杂度较高。"
		                     "在数据结构的实践中，我们经常需要处理字符串匹配问题。");}
    printf("测试文本长度: %d 字符\n", (int)strlen(text));
    const char* patterns[] = { "数据", "算法", "KMP", "字符串", "结构", "计算机", "匹配" };
    int patternCount = 7;

    printf("\n%-15s %-15s %-15s %-15s\n", "模式串", "BF耗时(us)", "KMP耗时(us)", "BST索引耗时(us)");
    printf("----------------------------------------------------------------------\n");

    for (int k = 0; k < patternCount; ++k) {
        const char* p = patterns[k];
        int m = strlen(p);
        if (m > strlen(text)) continue;

        // BF
        clock_t start = clock();
        int posBF = BF(text, p);
        clock_t end = clock();
        double timeBF = (double)(end - start) * 1000000.0 / CLOCKS_PER_SEC;

        // KMP
        start = clock();
        int posKMP = KMP(text, p);
        end = clock();
        double timeKMP = (double)(end - start) * 1000000.0 / CLOCKS_PER_SEC;

        // BST 索引（模拟：直接查找关键词，因为索引已建好）
        start = clock();
        int count = 0;
        int* ids = manager.getIndex().search(p, count);
        end = clock();
        double timeBST = (double)(end - start) * 1000000.0 / CLOCKS_PER_SEC;

        printf("%-15s %-15.2f %-15.2f %-15.2f\n", p, timeBF, timeKMP, timeBST);
    }
    printf("\n注：BST索引耗时仅包含搜索树的时间，不包含建索引时间。\n");
}

// ---------- 主程序 ----------
int main() {
    DocManagerWithIndex docs;
    docs.loadFromFile();
    UndoStack undoStack;
    SearchHistoryQueue searchHistory;

    int nextId = 1;
    for (int i = 0; i < docs.getLength(); ++i) {
        if (docs.getDoc(i)->id >= nextId)
            nextId = docs.getDoc(i)->id + 1;
    }

    while (true) {
        printf("\n╔══════════════════════════════════════════════════════════════════════╗\n");
        printf("║     简易搜索引擎 V4.0 （BST倒排索引 · 效率对比）                     ║\n");
        printf("╠══════════════════════════════════════════════════════════════════════╣\n");
        printf("║  1.添加文档  2.删除文档  3.修改文档  4.查看全部文档                ║\n");
        printf("║  5.搜索文档  6.撤销操作  7.查看搜索历史  8.保存并退出              ║\n");
        printf("║  9.算法效率对比测试 (BF vs KMP vs BST)                             ║\n");
        printf("╚══════════════════════════════════════════════════════════════════════╝\n");
        printf("请选择: ");

        int choice;
        scanf("%d", &choice);
        getchar();

        if (choice == 1) {
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
                Action act;
                act.type = OP_ADD;
                act.doc = doc;
                undoStack.push(act);
                nextId++;
            } else {
                printf("? 添加失败：文档库已满\n");
            }
        }
        else if (choice == 2) {
            int id;
            printf("请输入要删除的文档ID: ");
            scanf("%d", &id);
            getchar();
            Document* target = docs.findById(id);
            if (target) {
                Action act;
                act.type = OP_DELETE;
                act.doc = *target;
                undoStack.push(act);
                docs.deleteById(id);
                printf("? 删除成功（可撤销）\n");
            } else {
                printf("? 未找到ID为%d的文档\n", id);
            }
        }
        else if (choice == 3) {
            int id;
            printf("请输入要修改的文档ID: ");
            scanf("%d", &id);
            getchar();
            Document* doc = docs.findById(id);
            if (doc) {
                printf("当前文档信息：\n");
                printDoc(doc);
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
        else if (choice == 4) {
            printf("\n--- 全部文档列表 (共%d篇) ---\n", docs.getLength());
            if (docs.getLength() == 0)
                printf("暂无文档\n");
            else
                for (int i = 0; i < docs.getLength(); ++i)
                    printDoc(docs.getDoc(i));
        }
        else if (choice == 5) {
            printf("请输入搜索关键词: ");
            char keyword[MAX_CONTENT];
            fgets(keyword, MAX_CONTENT, stdin);
            keyword[strcspn(keyword, "\n")] = 0;
            if (strlen(keyword) == 0) {
                printf("关键词不能为空。\n");
                continue;
            }

            printf("\n请选择匹配算法:\n");
            printf("  1. BF (Brute-Force) 朴素匹配\n");
            printf("  2. KMP (Knuth-Morris-Pratt) 快速匹配\n");
            printf("  3. BST 索引搜索 (V4.0 新功能)\n");
            printf("请选择 (1/2/3): ");
            int algoChoice;
            scanf("%d", &algoChoice);
            getchar();
            if (algoChoice < 1 || algoChoice > 3) {
                printf("无效选择，默认使用 KMP。\n");
                algoChoice = 2;
            }

            printf("\n是否启用多维度筛选? (y/n): ");
            char yn;
            scanf("%c", &yn);
            getchar();
            Filter filter = {"", "", "", "", ""};
            if (yn == 'y' || yn == 'Y') {
                printf("  [筛选条件 - 直接回车表示不限]\n");
                printf("  栏目: "); fgets(filter.category, MAX_CATEGORY, stdin); filter.category[strcspn(filter.category, "\n")] = 0;
                printf("  作者: "); fgets(filter.author, MAX_AUTHOR, stdin); filter.author[strcspn(filter.author, "\n")] = 0;
                printf("  状态: "); fgets(filter.status, 20, stdin); filter.status[strcspn(filter.status, "\n")] = 0;
                printf("  起始日期(YYYY-MM-DD): "); fgets(filter.startDate, 20, stdin); filter.startDate[strcspn(filter.startDate, "\n")] = 0;
                printf("  结束日期(YYYY-MM-DD): "); fgets(filter.endDate, 20, stdin); filter.endDate[strcspn(filter.endDate, "\n")] = 0;
            }

            searchDocs(docs, keyword, algoChoice, filter, searchHistory);
        }
        else if (choice == 6) {
            Action act;
            if (!undoStack.pop(act)) {
                printf("没有可撤销的操作。\n");
                continue;
            }
            if (act.type == OP_ADD) {
                if (docs.deleteById(act.doc.id))
                    printf("? 已撤销添加（删除文档 ID=%d）\n", act.doc.id);
                else
                    printf("? 撤销失败：可能文档已被删除\n");
            }
            else if (act.type == OP_DELETE) {
                if (docs.addDoc(act.doc))
                    printf("? 已撤销删除（恢复文档 ID=%d）\n", act.doc.id);
                else
                    printf("? 撤销失败：文档库已满\n");
            }
            else if (act.type == OP_UPDATE) {
                int idx = docs.findIndexById(act.doc.id);
                if (idx != -1) {
                    docs.updateById(act.doc.id, act.doc.title, act.doc.content,
                                    act.doc.category, act.doc.author,
                                    act.doc.status, act.doc.publishDate);
                    printf("? 已撤销修改（恢复文档 ID=%d）\n", act.doc.id);
                } else {
                    docs.addDoc(act.doc);
                    printf("? 已撤销修改并恢复文档 ID=%d\n", act.doc.id);
                }
            }
        }
        else if (choice == 7) {
            searchHistory.display();
        }
        else if (choice == 8) {
            docs.saveToFile();
            printf("? 文档已保存，再见！\n");
            break;
        }
        else if (choice == 9) {
            compareAlgorithms(docs);
        }
        else {
            printf("? 无效选择，请重新输入\n");
        }
    }
    return 0;
}
