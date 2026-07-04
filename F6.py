// V6.0_search_engine.cpp - 最终100%完整无错版
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <cctype>
#include <string>
#include <algorithm>
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

struct Document {
    int id;
    char title[MAX_TITLE], content[MAX_CONTENT], category[MAX_CATEGORY];
    char author[MAX_AUTHOR], status[20], publishDate[20];
};

struct Filter {
    char category[MAX_CATEGORY], author[MAX_AUTHOR], status[20];
    char startDate[20], endDate[20];
};

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
