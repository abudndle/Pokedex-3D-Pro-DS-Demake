#include "title_audio.h"
#include <assert.h>
#include <stdio.h>
int main(int argc,char **argv){
    static P3DTitleCues cues;
    static P3DTitleAudio sound;
    assert(argc==12);
    assert(p3dTitleCuesLoad(&cues,argv[1],2));
    assert(cues.ready && cues.frames==2);
    assert(p3dTitleCueForFrame(&cues,0)==1);
    assert(p3dTitleCueForFrame(&cues,1)==2);
    assert(p3dTitleCueForFrame(&cues,2)==0);
    assert(p3dTitleCueForFrame(0,0)==0);
    assert(p3dTitleCuesLoad(&cues,argv[2],1));
    assert(p3dTitleCueForFrame(&cues,0)==1);
    assert(!p3dTitleCuesLoad(&cues,argv[1],1));
    assert(!cues.ready && p3dTitleCueForFrame(&cues,0)==0);
    for(int i=3;i<=6;i++){
        assert(!p3dTitleCuesLoad(&cues,argv[i],2));
        assert(!cues.ready);
    }
    assert(!p3dTitleCuesLoad(&cues,0,2));
    assert(!p3dTitleCuesLoad(&cues,argv[1],0));
    assert(!p3dTitleCuesLoad(0,argv[1],2));
    assert(p3dTitleAudioLoad(&sound,argv[7]));
    assert(sound.ready && sound.rate==16000 && sound.sample_count==32);
    assert(sound.pcm[1]==1 && sound.pcm[31]==31);
    for(int i=8;i<=11;i++){
        assert(!p3dTitleAudioLoad(&sound,argv[i]));
        assert(!sound.ready && !sound.sample_count);
    }
    assert(!p3dTitleAudioLoad(&sound,0));
    assert(!p3dTitleAudioLoad(0,argv[7]));
    puts("C118: private 3DS title cue maps and PCM16 validation: PASS");
    return 0;
}
