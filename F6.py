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

// ---------- 倒排索引 ----------
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
public:
    BSTIndex() : root(nullptr) {}
    ~BSTIndex() { clear(root); }
    void insert(const char* k, int id) { ins(root, k, id); }
    int* search(const char* k, int& num) { return find(root, k, num); }
    void reset() { clear(root); root = nullptr; }
    BSTNode* getRoot() { return root; }
};

// ---------- 字符串辅助 ----------
void toLowerStr(char* s) { for(int i=0; s[i]; i++) s[i] = tolower(s[i]); }
void splitWord(const char* src, char buf[][MAX_KEYWORD], int& num) {
    num = 0; char tmp[MAX_CONTENT]; strcpy(tmp, src);
    char* p = strtok(tmp, " .,!?;:\n\t");
    while(p && num < MAX_DOCS_PER_KEY*2) {
        if(strlen(p) > 1) { strcpy(buf[num], p); toLowerStr(buf[num]); num++; }
        p = strtok(nullptr, " .,!?;:\n\t");
    }
}

// ---------- 带索引和哈希的文档管理器 ----------
class DocManagerWithIndex : public DocManager {
    BSTIndex idx;
    HashTable docHash; 
    void rebuild() {
        idx.reset();
        for(int i=0; i<length; i++) {
            Document* d = getDoc(i);
            docHash.insert(d->id, d); 
            char word[MAX_DOCS_PER_KEY*2][MAX_KEYWORD];
            int wCnt; char all[MAX_CONTENT*2];
            sprintf(all, "%s %s", d->title, d->content);
            splitWord(all, word, wCnt);
            for(int j=0; j<wCnt; j++) idx.insert(word[j], d->id);
        }
    }
public:
    void loadFromFile() { DocManager::loadFromFile(); rebuild(); }
    bool addDoc(const Document& d) {
        bool ok = DocManager::addDoc(d);
        if(ok) { docHash.insert(d.id, getDoc(length-1)); idx.insert(d.title, d.id); } 
        return ok;
    }
    bool deleteById(int id) {
        bool ok = DocManager::deleteById(id);
        if(ok) rebuild();
        return ok;
    }
    BSTIndex& getIndex() { return idx; }
    HashTable& getHashTable() { return docHash; }
};

// ---------- BF / KMP 算法 ----------
int BF(const char* text, const char* pat) {
    int n=strlen(text), m=strlen(pat);
    for(int i=0; i<=n-m; i++) {
        int j; for(j=0; j<m; j++) if(text[i+j]!=pat[j]) break;
        if(j==m) return i;
    } return -1;
}
int KMP(const char* text, const char* pat) {
    int n=strlen(text), m=strlen(pat);
    int* nxt = new int[m]; int i=0, j=-1; nxt[0]=-1;
    while(i<m-1) { if(j==-1 || pat[i]==pat[j]) nxt[++i]=++j; else j=nxt[j]; }
    i=0, j=0; while(i<n && j<m) { if(j==-1 || text[i]==pat[j]){i++;j++;} else j=nxt[j]; }
    delete[] nxt; return (j==m) ? i-j : -1;
}

// ---------- 打印 HTML 格式 ----------
void printDocHTML(char* buffer, Document* d, const char* key) {
    char summary[100]; strncpy(summary, d->content, 80); summary[80] = 0;
    char* pos = strstr(d->content, key);
    char highlight[600] = "";
    if(pos) {
        char before[100], after[100];
        int start = pos - d->content; int end = start + strlen(key);
        int b_start = (start-20) > 0 ? start-20 : 0;
        strncpy(before, d->content + b_start, start - b_start); before[start - b_start]=0;
        strncpy(after, d->content + end, 20); after[20]=0;
        sprintf(highlight, "<span style='color:red'>%s【%s】%s</span>", before, key, after);
    } else { strcpy(highlight, d->content); }

    sprintf(buffer + strlen(buffer), 
        "<div style='border-left:4px solid #007bff; padding:10px; margin:10px 0; background:#fafafa;'>"
        "<b>ID:%d</b> 标题:%s <br> 栏目:%s | 作者:%s | 状态:%s <br> "
        "<b>摘要片段:</b> %s <br>"
        "<span style='font-size:12px;color:#888;'>%s</span>"
        "</div><hr>",
        d->id, d->title, d->category, d->author, d->status, highlight, d->publishDate);
}
