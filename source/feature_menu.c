#include "feature_menu.h"
#include <string.h>
static const P3DPage menu[]={P3D_PAGE_DEX,P3D_PAGE_SEARCH,P3D_PAGE_MOVES,P3D_PAGE_TYPES,P3D_PAGE_FAVORITES,P3D_PAGE_CHALLENGE,P3D_PAGE_SETTINGS,P3D_PAGE_ALBUM,P3D_PAGE_AR};
static const char *names[]={"MAIN MENU","POKEDEX","SEARCH","MOVE DEX","TYPE CHART","FAVORITES","CHALLENGE","SETTINGS","PHOTO ALBUM","AR CAMERA"};
const char *p3dPageName(P3DPage p){return p>=0&&p<P3D_PAGE_COUNT?names[p]:"UNKNOWN";}
void p3dMenuReset(P3DMenu *s){if(!s)return;memset(s,0,sizeof(*s));s->search_letter='A';s->type_defend2=-1;s->rotate=1;for(int i=0;i<P3D_FAVORITES_MAX;i++)s->favorites[i]=-1;}
size_t p3dMenuEntries(P3DCapabilities caps,P3DPage out[P3D_MENU_MAX]){size_t n=0;for(size_t i=0;i<sizeof(menu)/sizeof(menu[0]);i++){P3DPage p=menu[i];if(p==P3D_PAGE_AR&&!p3dCanEnterFeature(caps,P3D_FEATURE_AR))continue;if(out)out[n]=p;n++;}return n;}
int p3dMenuEnter(P3DMenu *s,P3DCapabilities caps,P3DPage page){if(!s||page<0||page>=P3D_PAGE_COUNT)return 0;if(page==P3D_PAGE_AR&&!p3dCanEnterFeature(caps,P3D_FEATURE_AR))return 0;s->page=page;s->cursor=0;return 1;}
int p3dFavoriteContains(const P3DMenu *s,int model){if(!s)return 0;for(int i=0;i<s->favorites_count;i++)if(s->favorites[i]==model)return 1;return 0;}
int p3dFavoriteToggle(P3DMenu *s,int model){if(!s||model<0||model>=738)return 0;for(int i=0;i<s->favorites_count;i++)if(s->favorites[i]==model){for(int j=i;j+1<s->favorites_count;j++)s->favorites[j]=s->favorites[j+1];s->favorites[--s->favorites_count]=-1;if(s->favorite_cursor>=s->favorites_count)s->favorite_cursor=0;return -1;}if(s->favorites_count>=P3D_FAVORITES_MAX)return 0;s->favorites[s->favorites_count++]=model;return 1;}
static const char *types[]={"NORMAL","FIRE","WATER","ELECTRIC","GRASS","ICE","FIGHTING","POISON","GROUND","FLYING","PSYCHIC","BUG","ROCK","GHOST","DRAGON","DARK","STEEL"};
const char *p3dTypeName(int t){return t>=0&&t<17?types[t]:"UNKNOWN";}
typedef struct{unsigned char a,d,m;} Match;
#define N 0
#define F 1
#define W 2
#define E 3
#define G 4
#define I 5
#define FI 6
#define PO 7
#define GR 8
#define FL 9
#define PS 10
#define BU 11
#define RO 12
#define GH 13
#define DR 14
#define DA 15
#define ST 16
#define X(a,d,m) {a,d,m}
static const Match table[]={
 X(N,RO,5),X(N,GH,0),X(N,ST,5),
 X(F,F,5),X(F,W,5),X(F,G,20),X(F,I,20),X(F,BU,20),X(F,RO,5),X(F,DR,5),X(F,ST,20),
 X(W,F,20),X(W,W,5),X(W,G,5),X(W,GR,20),X(W,RO,20),X(W,DR,5),
 X(E,W,20),X(E,E,5),X(E,G,5),X(E,GR,0),X(E,FL,20),X(E,DR,5),
 X(G,F,5),X(G,W,20),X(G,G,5),X(G,PO,5),X(G,GR,20),X(G,FL,5),X(G,BU,5),X(G,RO,20),X(G,DR,5),X(G,ST,5),
 X(I,F,5),X(I,W,5),X(I,G,20),X(I,I,5),X(I,GR,20),X(I,FL,20),X(I,DR,20),X(I,ST,5),
 X(FI,N,20),X(FI,I,20),X(FI,PO,5),X(FI,FL,5),X(FI,PS,5),X(FI,BU,5),X(FI,RO,20),X(FI,GH,0),X(FI,DA,20),X(FI,ST,20),
 X(PO,G,20),X(PO,PO,5),X(PO,GR,5),X(PO,RO,5),X(PO,GH,5),X(PO,ST,0),
 X(GR,F,20),X(GR,E,20),X(GR,G,5),X(GR,PO,20),X(GR,FL,0),X(GR,BU,5),X(GR,RO,20),X(GR,ST,20),
 X(FL,E,5),X(FL,G,20),X(FL,FI,20),X(FL,BU,20),X(FL,RO,5),X(FL,ST,5),
 X(PS,FI,20),X(PS,PO,20),X(PS,PS,5),X(PS,DA,0),X(PS,ST,5),
 X(BU,F,5),X(BU,G,20),X(BU,FI,5),X(BU,PO,5),X(BU,FL,5),X(BU,PS,20),X(BU,GH,5),X(BU,DA,20),X(BU,ST,5),
 X(RO,F,20),X(RO,I,20),X(RO,FI,5),X(RO,GR,5),X(RO,FL,20),X(RO,BU,20),X(RO,ST,5),
 X(GH,N,0),X(GH,PS,20),X(GH,GH,20),X(GH,DA,5),X(GH,ST,5),
 X(DR,DR,20),X(DR,ST,5),
 X(DA,FI,5),X(DA,PS,20),X(DA,GH,20),X(DA,DA,5),X(DA,ST,5),
 X(ST,F,5),X(ST,W,5),X(ST,E,5),X(ST,I,20),X(ST,RO,20),X(ST,ST,5)
};
int p3dTypeEffect(int a,int d){if(a<0||a>=17||d<0||d>=17)return -1;for(size_t i=0;i<sizeof(table)/sizeof(table[0]);i++)if(table[i].a==a&&table[i].d==d)return table[i].m;return 10;}
int p3dTypeEffectDual(int a,int d1,int d2){int p=p3dTypeEffect(a,d1);if(p<0)return -1;if(d2<0)return p;
 int q=p3dTypeEffect(a,d2);
 return q<0?-1:p*q/10;}
int p3dSearchNext(const char *const labels[],size_t count,int from,char initial,int dir){if(!labels||!count||!dir)return -1;if(initial>='a'&&initial<='z')initial=(char)(initial-('a'-'A'));for(size_t i=0;i<count;i++){int at=(int)(((long long)from+(long long)(i+1)*(dir>0?1:-1)+(long long)count*(count+2))%(long long)count);if(labels[at]){unsigned char c=(unsigned char)labels[at][0];if(c>='a'&&c<='z')c=(unsigned char)(c-('a'-'A'));if(c==(unsigned char)initial)return at;}}return -1;}
