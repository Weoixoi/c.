// V1.0_simple_search_engine.c
// 简易搜索引擎 V1.0 - 基础文档库管理功能
// 数据结构：线性表（顺序表）
// 编译运行：Dev-C++ 新建C文件，粘贴代码，F11编译运行

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_SIZE 100
#define MAX_TITLE 100
#define MAX_CONTENT 500
#define MAX_CATEGORY 20
#define MAX_AUTHOR 50
#define DATA_FILE "documents.txt"

typedef struct {
    int id;
    char title[MAX_TITLE];
    char content[MAX_CONTENT];
    char category[MAX_CATEGORY];
    char author[MAX_AUTHOR];
    char status[20];      // 草稿/已发布
    char publishDate[20]; // 发布日期
} Document;

typedef struct {
    Document data[MAX_SIZE];
    int length;
} DocList;

// 初始化线性表
void initList(DocList *list) {
    list->length = 0;
}

// 添加文档（尾部插入）
int addDoc(DocList *list, Document doc) {
    if (list->length >= MAX_SIZE) return 0;
    list->data[list->length] = doc;
    list->length++;
    return 1;
}

// 按ID删除（前移覆盖）
int deleteById(DocList *list, int id) {
    for (int i = 0; i < list->length; i++) {
        if (list->data[i].id == id) {
            for (int j = i; j < list->length - 1; j++) {
                list->data[j] = list->data[j + 1];
            }
            list->length--;
            return 1;
        }
    }
    return 0;
}

// 按ID修改
int updateById(DocList *list, int id, char *newTitle, char *newContent, 
               char *newCategory, char *newAuthor, char *newStatus, char *newDate) {
    for (int i = 0; i < list->length; i++) {
        if (list->data[i].id == id) {
            if (newTitle && strlen(newTitle) > 0) strcpy(list->data[i].title, newTitle);
            if (newContent && strlen(newContent) > 0) strcpy(list->data[i].content, newContent);
            if (newCategory && strlen(newCategory) > 0) strcpy(list->data[i].category, newCategory);
            if (newAuthor && strlen(newAuthor) > 0) strcpy(list->data[i].author, newAuthor);
            if (newStatus && strlen(newStatus) > 0) strcpy(list->data[i].status, newStatus);
            if (newDate && strlen(newDate) > 0) strcpy(list->data[i].publishDate, newDate);
            return 1;
        }
    }
    return 0;
}

// 按ID查找
Document* findById(DocList *list, int id) {
    for (int i = 0; i < list->length; i++) {
        if (list->data[i].id == id) return &list->data[i];
    }
    return NULL;
}

// 保存到文件
void saveToFile(DocList *list) {
    FILE *fp = fopen(DATA_FILE, "w");
    if (!fp) return;
    fprintf(fp, "%d\n", list->length);
    for (int i = 0; i < list->length; i++) {
        fprintf(fp, "%d\n", list->data[i].id);
        fprintf(fp, "%s\n", list->data[i].title);
        fprintf(fp, "%s\n", list->data[i].content);
        fprintf(fp, "%s\n", list->data[i].category);
        fprintf(fp, "%s\n", list->data[i].author);
        fprintf(fp, "%s\n", list->data[i].status);
        fprintf(fp, "%s\n", list->data[i].publishDate);
    }
    fclose(fp);
}

// 从文件加载
void loadFromFile(DocList *list) {
    FILE *fp = fopen(DATA_FILE, "r");
    if (!fp) return;
    int n;
    fscanf(fp, "%d\n", &n);
    for (int i = 0; i < n && i < MAX_SIZE; i++) {
        Document doc;
        fscanf(fp, "%d\n", &doc.id);
        fgets(doc.title, MAX_TITLE, fp); doc.title[strcspn(doc.title, "\n")] = 0;
        fgets(doc.content, MAX_CONTENT, fp); doc.content[strcspn(doc.content, "\n")] = 0;
        fgets(doc.category, MAX_CATEGORY, fp); doc.category[strcspn(doc.category, "\n")] = 0;
        fgets(doc.author, MAX_AUTHOR, fp); doc.author[strcspn(doc.author, "\n")] = 0;
        fgets(doc.status, 20, fp); doc.status[strcspn(doc.status, "\n")] = 0;
        fgets(doc.publishDate, 20, fp); doc.publishDate[strcspn(doc.publishDate, "\n")] = 0;
        addDoc(list, doc);
    }
    fclose(fp);
}

// 打印单个文档
void printDoc(Document *doc) {
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

int main() {
    DocList docs;
    initList(&docs);
    loadFromFile(&docs);
    
    // 计算下一个可用ID
    int nextId = 1;
    for (int i = 0; i < docs.length; i++) {
        if (docs.data[i].id >= nextId) nextId = docs.data[i].id + 1;
    }
    
    while (1) {
        printf("\n╔════════════════════════════════════════════════════════════╗\n");
        printf("║     简易搜索引擎 V1.0 - 基础文档库管理功能                  ║\n");
        printf("╠════════════════════════════════════════════════════════════╣\n");
        printf("║  1. 添加文档      2. 删除文档      3. 修改文档              ║\n");
        printf("║  4. 查看全部文档  5. 保存并退出                             ║\n");
        printf("╚════════════════════════════════════════════════════════════╝\n");
        printf("请选择: ");
        
        int choice;
        scanf("%d", &choice);
        getchar();
        
        if (choice == 1) {
            printf("\n--- 添加新文档 ---\n");
            Document doc;
            doc.id = nextId;
            printf("标题: "); fgets(doc.title, MAX_TITLE, stdin); doc.title[strcspn(doc.title, "\n")] = 0;
            printf("内容: "); fgets(doc.content, MAX_CONTENT, stdin); doc.content[strcspn(doc.content, "\n")] = 0;
            printf("栏目(财经/科技/时尚): "); fgets(doc.category, MAX_CATEGORY, stdin); doc.category[strcspn(doc.category, "\n")] = 0;
            printf("作者: "); fgets(doc.author, MAX_AUTHOR, stdin); doc.author[strcspn(doc.author, "\n")] = 0;
            printf("状态(草稿/已发布): "); fgets(doc.status, 20, stdin); doc.status[strcspn(doc.status, "\n")] = 0;
            printf("发布日期(YYYY-MM-DD): "); fgets(doc.publishDate, 20, stdin); doc.publishDate[strcspn(doc.publishDate, "\n")] = 0;
            
            if (addDoc(&docs, doc)) {
                printf("✓ 添加成功！文档ID: %d\n", nextId);
                nextId++;
            } else {
                printf("✗ 添加失败：文档库已满\n");
            }
        }
        else if (choice == 2) {
            int id;
            printf("请输入要删除的文档ID: ");
            scanf("%d", &id);
            getchar();
            if (deleteById(&docs, id)) {
                printf("✓ 删除成功\n");
            } else {
                printf("✗ 未找到ID为%d的文档\n", id);
            }
        }
        else if (choice == 3) {
            int id;
            printf("请输入要修改的文档ID: ");
            scanf("%d", &id);
            getchar();
            Document *doc = findById(&docs, id);
            if (doc) {
                printf("当前文档信息：\n");
                printDoc(doc);
                
                char newTitle[MAX_TITLE] = "";
                char newContent[MAX_CONTENT] = "";
                char newCategory[MAX_CATEGORY] = "";
                char newAuthor[MAX_AUTHOR] = "";
                char newStatus[20] = "";
                char newDate[20] = "";
                
                printf("\n(直接回车表示不修改)\n");
                printf("新标题 [%s]: ", doc->title); fgets(newTitle, MAX_TITLE, stdin); newTitle[strcspn(newTitle, "\n")] = 0;
                printf("新内容 [%s...]: ", doc->content); fgets(newContent, MAX_CONTENT, stdin); newContent[strcspn(newContent, "\n")] = 0;
                printf("新栏目 [%s]: ", doc->category); fgets(newCategory, MAX_CATEGORY, stdin); newCategory[strcspn(newCategory, "\n")] = 0;
                printf("新作者 [%s]: ", doc->author); fgets(newAuthor, MAX_AUTHOR, stdin); newAuthor[strcspn(newAuthor, "\n")] = 0;
                printf("新状态 [%s]: ", doc->status); fgets(newStatus, 20, stdin); newStatus[strcspn(newStatus, "\n")] = 0;
                printf("新日期 [%s]: ", doc->publishDate); fgets(newDate, 20, stdin); newDate[strcspn(newDate, "\n")] = 0;
                
                updateById(&docs, id, newTitle, newContent, newCategory, newAuthor, newStatus, newDate);
                printf("✓ 修改成功\n");
            } else {
                printf("✗ 未找到ID为%d的文档\n", id);
            }
        }
        else if (choice == 4) {
            printf("\n--- 全部文档列表 (共%d篇) ---\n", docs.length);
            if (docs.length == 0) {
                printf("暂无文档\n");
            } else {
                for (int i = 0; i < docs.length; i++) {
                    printDoc(&docs.data[i]);
                }
            }
        }
        else if (choice == 5) {
            saveToFile(&docs);
            printf("✓ 文档已保存，再见！\n");
            break;
        }
        else {
            printf("✗ 无效选择，请重新输入\n");
        }
    }
    return 0;
}
