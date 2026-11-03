#include "resume_state.h"
#include "dex_search.h"
#include "photo_album.h"
#include "records.h"
#include <stdio.h>
#include <string.h>
#define P3RV_V1_SIZE 32u
#define P3RV_V2_SIZE 48u
#define P3RV_V3_SIZE 80u
#define P3RV_V4_SIZE 144u /* Active Challenge only */
#define P3RV_V5_SIZE 96u /* Exact Pokédex detail tab only */
static unsigned r16(const unsigned char *p){return (unsigned)p[0]|((unsigned)p[1]<<8);}
static uint32_t r32(const unsigned char *p){
    return (uint32_t)r16(p)|((uint32_t)r16(p+2)<<16);
}
static void w16(unsigned char *p,unsigned n){
    p[0]=(unsigned char)n;p[1]=(unsigned char)(n>>8);
}
static void w32(unsigned char *p,uint32_t n){
    w16(p,n);w16(p+2,n>>16);
}
static uint32_t checksum(const unsigned char *p,unsigned n){
    uint32_t crc=0xffffffffu;
    for(unsigned i=0;i<n;i++){
        crc^=p[i];
        for(unsigned k=0;k<8;k++)
            crc=(crc>>1)^((crc&1u)?0xedb88320u:0u);
    }
    return crc^0xffffffffu;
}
static int valid_query(const char query[13]){
    unsigned i;
    for(i=0;i<13;i++){
        unsigned c=(unsigned char)query[i];
        if(c==0){
            /* Canonical NUL padding prevents stale input from being saved. */
            for(unsigned j=i+1;j<13;j++)if(query[j]!=0)return 0;
            return 1;
        }
        if(i>=12 || c<'A'||c>'Z')return 0;
    }
    return 0;
}
/* Validate every identity before reviving live quiz state. Keep these
 * seven legacy mode ranges synchronized with challenge.c. */
static int valid_quiz(const P3DResumeState *s){
 static const int first[P3D_CHALLENGE_MODES]={493,0,151,251,386,0,0};
 static const int last[P3D_CHALLENGE_MODES]={648,150,250,385,492,648,648};
 const P3DChallenge *q=&s->quiz;
 int lower,upper,answered;
 if(!s->quiz_active)return 1;
 if(s->quiz_active!=1 || s->home || s->page!=P3D_PAGE_CHALLENGE ||
    s->challenge_correct_total>s->challenge_answer_total ||
    s->challenge_answer_total>100000000u ||
    q->mode<0 || q->mode>=P3D_CHALLENGE_MODES ||
    q->mode_cursor!=q->mode || s->challenge_mode!=(uint8_t)q->mode ||
    (q->stage!=P3D_CHALLENGE_QUESTION&&q->stage!=P3D_CHALLENGE_REVIEW) ||
    q->seed==0u || q->question<0 || q->question>=P3D_CHALLENGE_QUESTIONS ||
    q->selected<0 || q->selected>=P3D_CHALLENGE_OPTIONS ||
    q->correct<0 || q->correct>=P3D_CHALLENGE_OPTIONS ||
    q->clue_page<0 || q->clue_page>3 ||
    (q->mode!=P3D_CHALLENGE_TEXT_MODE && q->clue_page!=0))
    return 0;
 if(q->mode==P3D_CHALLENGE_TEXT_MODE &&
    s->challenge_answer_total<P3D_CHALLENGE_TEXT_UNLOCK)return 0;
 answered=q->stage==P3D_CHALLENGE_REVIEW;
 if(q->score<0 || q->score>q->question+answered ||
    (answered && q->selected==q->correct && q->score==0) ||
    (answered && q->selected!=q->correct && q->score>q->question) ||
    (uint32_t)q->score>s->challenge_correct_total ||
    s->challenge_answer_total<(uint32_t)(q->question+answered))return 0;
 lower=first[q->mode];upper=last[q->mode];
 if(q->pokemon<lower || q->pokemon>upper ||
    q->asked[q->question]!=q->pokemon ||
    q->choices[q->correct]!=q->pokemon)return 0;
 for(int i=0;i<P3D_CHALLENGE_QUESTIONS;i++){
   if(i<=q->question){
     if(q->asked[i]<lower || q->asked[i]>upper)return 0;
     for(int j=0;j<i;j++)if(q->asked[i]==q->asked[j])return 0;
   }else if(q->asked[i]!=0)return 0;
 }
 for(int i=0;i<P3D_CHALLENGE_OPTIONS;i++){
   if(q->choices[i]<lower || q->choices[i]>upper)return 0;
   for(int j=0;j<i;j++)if(q->choices[j]==q->choices[i])return 0;
 }
 return 1;
}
int p3dResumeStateValid(const P3DResumeState *s){
    return s&&s->home<=1&&s->page<P3D_PAGE_COUNT &&
        s->highlight<P3D_MENU_MAX&&s->records_tab<=2&&
        s->dex<649&&s->move<559&&s->selected_dex<649&&
        s->album_page<=999&&s->album_selected<P3D_ALBUM_PAGE_MAX&&
        s->records_recent_cursor<P3D_RECORD_RECENT&&
        s->move_show_effect<=1&&s->search_region<P3D_DEX_REGIONS&&
        s->search_scope<P3D_DEX_SCOPE_COUNT&&
        s->search_field<=P3D_DEX_SEARCH_DESCRIPTION&&
        s->favorite_cursor<P3D_FAVORITES_MAX&&
        s->move_text_offset<=4096&&
        valid_query(s->search_query)&&
        (s->search_letter==0||(s->search_letter>='A'&&s->search_letter<='Z'))&&
        s->challenge_mode<7&&s->type_attack<17&&s->type_defend<17&&
        s->type_defend2_plus_one<=17&&s->favorites_selected<P3D_FAVORITES_MAX&&
        s->quiz_active<=1 && valid_quiz(s) && s->dex_detail_tab<=4 &&
        (!s->dex_detail_tab || (!s->home && !s->quiz_active &&
         s->page==P3D_PAGE_DEX));
}
/* P3RC wins if it already contains a completed round newer than the
 * live review's recorded-round generation. P3SV may lag behind a review
 * checkpoint, but can never roll the counters backwards on restore. */
int p3dResumeCanRestoreQuiz(const P3DResumeState *s,
                            uint32_t progress_correct,uint32_t progress_answers,
                            uint32_t recorded_rounds){
 return s && s->quiz_active && p3dResumeStateValid(s) &&
        s->challenge_recorded_rounds==recorded_rounds &&
        s->challenge_answer_total>=progress_answers &&
        s->challenge_correct_total>=progress_correct;
}
static int file_path(char path[256],const char *base,int slot){
    int n;
    if(!base||!*base)return 0;
    n=snprintf(path,256,"%s_resume_%c.sav",base,slot?'B':'A');
    return n>0&&n<256;
}
static unsigned pack(unsigned char b[P3RV_V4_SIZE],const P3DResumeState *s,uint32_t seq){
    unsigned size=s->quiz_active?P3RV_V4_SIZE:
                  (s->dex_detail_tab?P3RV_V5_SIZE:P3RV_V3_SIZE);
    memset(b,0,P3RV_V4_SIZE);
    memcpy(b,"P3RV",4);b[4]=s->quiz_active?4:(s->dex_detail_tab?5:3);
    w32(b+8,seq);
    b[12]=s->home;b[13]=s->page;b[14]=s->highlight;b[15]=s->records_tab;
    w16(b+16,s->dex);w16(b+18,s->move);
    w16(b+20,s->selected_dex);w16(b+22,s->album_page);
    w16(b+24,s->selected_form);
    b[26]=s->album_selected;b[27]=s->records_recent_cursor;
    b[28]=s->move_show_effect;b[29]=s->search_region;
    b[30]=s->search_scope;b[31]=s->search_field;
    w16(b+32,s->move_text_offset);
    w16(b+34,s->menu_cursor);
    b[36]=s->favorite_cursor;
    memcpy(b+44,s->search_query,13);
    b[57]=s->search_letter;b[58]=s->challenge_mode;
    b[59]=s->type_attack;b[60]=s->type_defend;
    b[61]=s->type_defend2_plus_one;b[62]=s->favorites_selected;
    if(s->quiz_active){
        const P3DChallenge *q=&s->quiz;
        b[76]=1;b[77]=(unsigned char)q->stage;
        b[78]=(unsigned char)q->mode;b[79]=(unsigned char)q->question;
        b[80]=(unsigned char)q->score;b[81]=(unsigned char)q->selected;
        b[82]=(unsigned char)q->correct;b[83]=(unsigned char)q->clue_page;
        w16(b+84,(unsigned)q->pokemon);
        for(int i=0;i<P3D_CHALLENGE_OPTIONS;i++)
            w16(b+86+2*i,(unsigned)q->choices[i]);
        for(int i=0;i<P3D_CHALLENGE_QUESTIONS;i++)
            w16(b+94+2*i,(unsigned)q->asked[i]);
        w32(b+114,q->seed);
        w32(b+118,s->challenge_answer_total);
        w32(b+122,s->challenge_correct_total);
        w32(b+126,s->challenge_recorded_rounds);
        w32(b+140,checksum(b,140));
    }else if(s->dex_detail_tab){
        b[76]=s->dex_detail_tab;
        w32(b+92,checksum(b,92));
    }else w32(b+76,checksum(b,76));
    return size;
}
static int unpack(const unsigned char *b,unsigned size,
                  P3DResumeState *s,uint32_t *seq){
    unsigned version, crc_offset;
    if(size<P3RV_V1_SIZE||memcmp(b,"P3RV",4)!=0||
       b[5]!=0||r16(b+6)!=0)return 0;
    version=b[4];
    if(version==1 && size==P3RV_V1_SIZE && r32(b+24)==0){
        crc_offset=28;
    }else if(version==2 && size==P3RV_V2_SIZE){
        for(unsigned i=37;i<44;i++)if(b[i]!=0)return 0;
        crc_offset=44;
    }else if((version==3 && size==P3RV_V3_SIZE) ||
             (version==4 && size==P3RV_V4_SIZE) ||
             (version==5 && size==P3RV_V5_SIZE)){
        for(unsigned i=37;i<44;i++)if(b[i]!=0)return 0;
        for(unsigned i=63;i<76;i++)if(b[i]!=0)return 0;
        if(version==4){
          if(b[76]!=1)return 0; /* v4 must actually contain a quiz */
          for(unsigned i=130;i<140;i++)if(b[i]!=0)return 0;
        }
        if(version==5){
          if(b[76]<1 || b[76]>4)return 0;
          for(unsigned i=77;i<92;i++)if(b[i]!=0)return 0;
        }
        crc_offset=version==4?140:(version==5?92:76);
    }else return 0;
    if(r32(b+crc_offset)!=checksum(b,crc_offset))return 0;
    memset(s,0,sizeof(*s));
    *seq=r32(b+8);s->home=b[12];s->page=b[13];
    s->highlight=b[14];s->records_tab=b[15];
    s->dex=(uint16_t)r16(b+16);s->move=(uint16_t)r16(b+18);
    s->selected_dex=(uint16_t)r16(b+20);s->album_page=(uint16_t)r16(b+22);
    if(version>=2){
        s->selected_form=(uint16_t)r16(b+24);
        s->album_selected=b[26];s->records_recent_cursor=b[27];
        s->move_show_effect=b[28];s->search_region=b[29];
        s->search_scope=b[30];s->search_field=b[31];
        s->move_text_offset=(uint16_t)r16(b+32);
        s->menu_cursor=(uint16_t)r16(b+34);
        s->favorite_cursor=b[36];
    }
    if(version>=3){
        memcpy(s->search_query,b+44,13);
        s->search_letter=b[57];s->challenge_mode=b[58];
        s->type_attack=b[59];s->type_defend=b[60];
        s->type_defend2_plus_one=b[61];s->favorites_selected=b[62];
    }
    if(version==5)s->dex_detail_tab=b[76];
    if(version==4){
        P3DChallenge *q=&s->quiz;
        s->quiz_active=1;
        q->stage=(P3DChallengeStage)b[77];
        q->mode=q->mode_cursor=(int)b[78];
        q->question=(int)b[79];q->score=(int)b[80];
        q->selected=(int)b[81];q->correct=(int)b[82];
        q->clue_page=(int)b[83];q->pokemon=(int)r16(b+84);
        for(int i=0;i<P3D_CHALLENGE_OPTIONS;i++)
            q->choices[i]=(int)r16(b+86+2*i);
        for(int i=0;i<P3D_CHALLENGE_QUESTIONS;i++)
            q->asked[i]=(int)r16(b+94+2*i);
        q->seed=r32(b+114);
        s->challenge_answer_total=r32(b+118);
        s->challenge_correct_total=r32(b+122);
        s->challenge_recorded_rounds=r32(b+126);
    }
    return p3dResumeStateValid(s);
}
static int read_slot(const char *base,int slot,P3DResumeState *out,uint32_t *seq){
    char name[256];unsigned char b[P3RV_V4_SIZE];FILE *f;unsigned size;int ok;
    if(!file_path(name,base,slot)||(f=fopen(name,"rb"))==NULL)return 0;
    size=(unsigned)fread(b,1,P3RV_V4_SIZE,f);
    ok=!ferror(f)&&fgetc(f)==EOF&&!ferror(f);
    fclose(f);
    return ok&&unpack(b,size,out,seq);
}
static int newer(uint32_t a,uint32_t b){
    uint32_t delta=a-b;
    return delta!=0u&&delta<0x80000000u;
}
int p3dResumeLoad(const char *base,P3DResumeState *out){
    P3DResumeState a,b;uint32_t sa=0,sb=0;int va,vb;
    if(!out)return 0;
    va=read_slot(base,0,&a,&sa);vb=read_slot(base,1,&b,&sb);
    if(!va&&!vb)return 0;
    *out=va&&(!vb||!newer(sb,sa))?a:b;
    return 1;
}
int p3dResumeStore(const char *base,const P3DResumeState *s){
    P3DResumeState a,b;uint32_t sa=0,sb=0,seq=1;
    int va,vb,slot;char name[256];unsigned char bytes[P3RV_V4_SIZE];FILE *f;unsigned size;
    if(!p3dResumeStateValid(s))return 0;
    va=read_slot(base,0,&a,&sa);vb=read_slot(base,1,&b,&sb);
    if(va&&vb){
        int active=newer(sb,sa)?1:0;
        slot=1-active;seq=(active?sb:sa)+1;
    }else if(va){slot=1;seq=sa+1;}
    else if(vb){slot=0;seq=sb+1;}
    else slot=0;
    if(!file_path(name,base,slot))return 0;
    size=pack(bytes,s,seq);
    f=fopen(name,"wb");if(!f)return 0;
    if(fwrite(bytes,1,size,f)!=size||fflush(f)!=0){
        fclose(f);return 0;
    }
    return fclose(f)==0;
}
int p3dResumeApply(const P3DResumeState *s,P3DCapabilities caps,
                   int *home,P3DMenu *menu,int *highlight){
    if(!p3dResumeStateValid(s)||!home||!menu||!highlight)return 0;
    /* Old P3RV saves may refer to a longer development menu. */
    size_t entries=p3dMenuEntries(caps,NULL);
    *highlight=s->highlight<entries?s->highlight:(int)(entries-1);
    if(s->home){*home=1;return 1;}
    if(s->page==P3D_PAGE_AR&&!p3dCanEnterFeature(caps,P3D_FEATURE_AR)){
        *home=1;return 1;
    }
    if(s->page==P3D_PAGE_HOME){*home=1;return 1;}
    if(!p3dMenuEnter(menu,caps,(P3DPage)s->page)){
        *home=1;return 1;
    }
    *home=0;
    menu->selected_dex=s->selected_dex;
    menu->cursor=s->menu_cursor;
    /* Favorites list comes from P3SV. Never restore a cursor beyond it. */
    menu->favorite_cursor=(menu->favorites_count>0&&
        s->favorite_cursor<(unsigned)menu->favorites_count)
        ?s->favorite_cursor:0;
    return 1;
}
int p3dResumeRestoreBoot(const char *base,P3DResumeState *restored,
                         P3DCapabilities caps,int *home,
                         P3DMenu *menu,int *highlight){
    P3DResumeState checkpoint;
    if(!restored||!p3dResumeLoad(base,&checkpoint)||
       !p3dResumeApply(&checkpoint,caps,home,menu,highlight))
        return 0;
    *restored=checkpoint;
    return 1;
}
