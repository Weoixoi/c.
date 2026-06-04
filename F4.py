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
