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
