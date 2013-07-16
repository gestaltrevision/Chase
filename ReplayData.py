from Settings import *
from Constants import *
from psychopy import visual, core, event,gui
from psychopy.misc import pix2deg
import numpy as np
from scipy.interpolate import interp1d
from datetime import datetime
from evalETdata import tseries2eventlist, t2f, selectAgentTRACKING

class Trajectory():
    def __init__(self,gazeData,maze=None,wind=None,
            highlightChase=False,phase=1,eyes=1):
        self.wind=wind
        self.phase=phase
        self.cond=gazeData.oldtraj.shape[1]
        self.pos=[]
        self.eyes=eyes
        # determine common time intervals
        g=gazeData.getGaze(phase)
        ts=max(g[0,0], gazeData.fs[0,1])
        te=min(g[-1,0],gazeData.fs[-1,1])
        self.t=np.linspace(ts,te,int(round((te-ts)*Q.refreshRate/1000.0)))
        # put data together
        g=gazeData.getGaze(phase,hz=self.t)
        tr=gazeData.getTraj(hz=self.t)
        if eyes==1: g=g[:,[7,8]];g=np.array(g,ndmin=3)
        else: g=np.array([g[:,[1,2]],g[:,[4,5]]])
        
        g=np.rollaxis(g,0,2)
        
        self.pos=np.concatenate([tr,g],axis=1)
        try:
            if type(self.wind)==type(None):
                self.wind=Q.initDisplay()
            #if gazeData!=None:
            self.cond+=1
            if eyes==2: self.cond+=1
            clrs=np.ones((self.cond,3))
            clrs[-1,[0,1]]=0
            if eyes==2: clrs[-2,[0,1]]=0
            if highlightChase: clrs[0,[0,2]]=0; clrs[1,[1,2]]=0
            #print clrs
            self.elem=visual.ElementArrayStim(self.wind,fieldShape='sqr',
                nElements=self.cond,sizes=Q.agentSize,colors=clrs,interpolate=False,
                colorSpace='rgb',elementMask='circle',elementTex=None)
            if type(maze)!=type(None):
                self.maze=maze
                self.maze.draw(wind)
        except:
            self.wind.close()
            raise
    def showFrame(self,positions):
        try:
            try:
                self.maze.draw(wind)
            except AttributeError: pass
            self.elem.setXYs(positions)
            self.elem.draw()
            self.wind.flip()
        except: 
            self.wind.close()
            raise
    
    def play(self,tlag=0):
        """
            shows the trial as given by TRAJECTORIES
        """
        try:
            self.wind.flip()
            playing=False
            #t0=core.getTime()
            step=1000/float(Q.refreshRate)
            position=np.zeros((self.cond,2))
            sel=0; self.f=0
            while True:#self.f<self.pos.shape[0]:
                self.f=min(self.f,self.pos.shape[0]-1)
                self.f=max(0,self.f)
                position=self.pos[self.f,:,:]
                if self.phase==1:
                    clrs=np.copy(self.elem.colors)
                    ags=self.highlightedAgents()
                    #print self.t[f], ags
                    for a in range(self.cond-self.eyes): 
                        if a in ags: clrs[a,:]=[0,1,0]
                        else: clrs[a,:]=[1,1,1]
                    self.elem.setColors(clrs)
##                elif self.phase==2:
##                    if sel<1 and f>self.gazeData.behdata[8]*Q.refreshRate:
##                        clrs=np.copy(self.elem.colors)
##                        clrs[int(self.gazeData.behdata[7]),:]=np.array([1,1,0])
##                        self.elem.setColors(clrs);sel+=1
##                    if sel<2 and f>self.gazeData.behdata[10]*Q.refreshRate:
##                        clrs=np.copy(self.elem.colors)
##                        clrs[int(self.gazeData.behdata[9]),:]=np.array([1,1,0])
##                        self.elem.setColors(clrs);sel+=1
                self.showFrame(position)
                if playing and tlag>0: core.wait(tlag)
                for key in event.getKeys():
                    if key in ['escape']:
                        self.wind.close()
                        return
                        #core.quit()
                    #print key
                    if key=='space': playing= not playing
                    if key=='l': self.f=self.f+1
                    if key=='k': self.f=self.f-1
                    if key=='semicolon': self.f=self.f+10
                    if key=='j': self.f=self.f-10
                    if key=='s': self.save=True
                if playing and self.f>=self.pos.shape[0]-1:  playing=False
                if not playing: core.wait(0.01)
                if playing: self.f+=2
            self.wind.flip()
            #print core.getTime() - t0
            self.wind.close()
        except: 
            self.wind.close()
            raise
    def highlightedAgents(self): return []
        
class GazePoint(Trajectory):
    def __init__(self, gazeData,wind=None):
        self.gazeData=gazeData
        self.wind=wind
        self.pos=[]
        g=self.gazeData.getGaze()
        self.trialDur=g.shape[0]/self.gazeData.hz*1000
        step=1000/float(Q.refreshRate)
        tcur=np.arange(0,self.trialDur-3*step,step)
        self.t=tcur
        step=1000/float(gazeData.hz)
        t=np.arange(0,g.shape[0]*step,step)
        self.gaze=np.array((interpRange(t,g[:,1],tcur),
            interpRange(t,g[:,2],tcur)))
        try:
            if type(self.wind)==type(None):
                self.wind=Q.initDisplay()
            self.cond=1
            self.gazeDataRefresh=gazeData.hz
            clrs=np.ones((self.cond,3))
            self.elem=visual.ElementArrayStim(self.wind,fieldShape='sqr',
                nElements=self.cond,sizes=Q.agentSize,rgbs=clrs,
                elementMask='circle',elementTex=None)
        except:
            self.wind.close()
            raise

class ETReplay(Trajectory):
    def __init__(self,gazeData,**kwargs):
        wind = kwargs.get('wind',None)
        if wind is None: wind = Q.initDisplay((1280,1100))
        Trajectory.__init__(self,gazeData,wind=wind,**kwargs)
        self.gazeData=gazeData
        self.mouse = event.Mouse(True,None,self.wind)
        try:
            indic=['Velocity','Acceleration','Saccade','Fixation']#,'OL Pursuit','CL Pursuit','HEV','Tracking']
            self.lim=([0,450],[-42000,42000],[0,1],[0,1],[0,1],[0,1],[0,1],[0,1])# limit of y axis
            self.span=(0.9,0.9,0.6,0.6,0.6,0.6,0.6,0.6)# height of the window taken by graph
            self.offset=(0.1,0.1,0.2,0.2,0.2,0.2,0.2,0.2)
            fhandles=[self.gazeData.getVelocity,self.gazeData.getAcceleration,
                      self.gazeData.getSaccades, self.gazeData.getFixations,
                      self.gazeData.getOLP,self.gazeData.getCLP,
                      self.gazeData.getHEV,self.gazeData.getTracking]
            self.ws=30; self.sws=150.0 # selection window size
            ga=[7.8337, 18.7095,-13.3941+5,13.3941+5] # graph area
            self.ga=ga
            mid=ga[0]+(ga[1]-ga[0])/2.0
            inc=(ga[3]-ga[2])/float(len(indic));self.inc=inc
            self.spar=(0,-12,4) #parameters for selection tool, posx, posy, height
            frame=[visual.Line(self.wind,(ga[0],ga[3]),(ga[0],ga[2]),lineWidth=4.0),
                visual.Line(self.wind,(-ga[1],ga[3]),(ga[1],ga[3]),lineWidth=4.0),
                visual.Line(self.wind,(mid,ga[3]),(mid,ga[2]),lineWidth=2.0),
                visual.Line(self.wind,(ga[1],ga[3]),(ga[1],ga[2]),lineWidth=4.0),
                visual.Line(self.wind, (-ga[1],ga[2]),(ga[1],ga[2]),lineWidth=4.0),
                visual.Line(self.wind, (-ga[1],ga[2]),(-ga[1],ga[3]),lineWidth=4.0),
                visual.Rect(self.wind, width=ga[1]*2,height=self.spar[2], pos=(self.spar[0],self.spar[1]),lineWidth=4.0),
                visual.Line(self.wind,(0,self.spar[1]+self.spar[2]/2.0),(0,self.spar[1]-self.spar[2]/2.0),lineWidth=2.0)
                ]
            self.seltoolrect=frame[6]
            self.graphs=[]
            self.sacrects=[]
            for i in range(15): self.sacrects.append(visual.Rect(self.wind,
                height=self.spar[2],width=2,fillColor='blue',opacity=0.5,lineColor='blue'))
            self.selrects=[]
            for i in range(15): self.selrects.append(visual.Rect(self.wind,
                height=self.spar[2],width=1,fillColor='red',opacity=0.5,lineColor='red'))
            for f in range(len(indic)):      
                frame.append(visual.Line(self.wind,(ga[0],ga[3]-(f+1)*inc),
                    (ga[1],ga[3]-(f+1)*inc),lineWidth=4.0))
                frame.append(visual.TextStim(self.wind,indic[f],
                    pos=(ga[0]+0.1,ga[3]-0.1-f*inc),
                    alignHoriz='left',alignVert='top',height=0.5))
                self.graphs.append(visual.ShapeStim(self.wind,
                                closeShape=False,lineWidth=2.0))
                self.graphs[f].setAutoDraw(True)
                
            self.frame=visual.BufferImageStim(self.wind,stim=frame)
            self.tmsg=visual.TextStim(self.wind,color=(0.5,0.5,0.5),pos=(-15,-9))
            self.msg= visual.TextStim(self.wind,color=(0.5,0.5,0.5),
                pos=(0,-9),text=' ',wrapWidth=20)
            self.msg.setAutoDraw(True)
            self.gData=[]
            for g in range(len(indic)):
                yOld=fhandles[g](self.phase,hz=self.t)
                self.gData.append(yOld)
            self.sev=[]
            scale=Q.refreshRate/self.gazeData.hz
            for gs in self.gazeData.sev:
                s=int(np.round(scale*gs[0]))
                e=min(len(self.t)-1,max(s+1, int(np.round(scale*gs[1]))))
                self.sev.append([s,e,gs[0],gs[1]])
            for gs in self.gazeData.bev:
                s=int(np.round(scale*gs[0]))
                e=min(len(self.t)-1,max(s+1, int(np.round(scale*gs[1]))))
                self.sev.append([s,e,gs[0],gs[1]])
            self.selected=[[]]
            try:
                for tr in self.gazeData.track:
                    s=int(np.round(scale*tr[0]))
                    e=min(len(self.t)-1,max(s+1, int(np.round(scale*tr[1]))))
                    self.selected[0].append([self.t[s],s,tr[0],self.t[e],e,tr[1],tr[2],False])
            except: print 'Tracking events not available'
            self.pos[:,:,0]-=6 # shift agents locations on the screen
            self.pos[:,:,1]+=5
            self.wind.flip()
            self.released=False # mouse key flag
            self.save=False # flag for save selection tool data
        except:
            self.wind.close()
            raise
    def showFrame(self,positions):
        fs=max(0,self.f-self.ws)
        fe=min(self.f+self.ws,self.gData[0].shape[0]-1)
        #xveldata=np.array(self.t[fs:fe], ndmin=2)
        unit = (self.ga[1]-self.ga[0])/float(self.ws)/2.0
        step=(2*self.ws-(fe-fs))*unit
        if fs<self.ws: s=self.ga[0]+step
        else: s=self.ga[0]
        if fe>self.gData[0].size-self.ws: e=self.ga[1]-step
        else: e=self.ga[1]
        xveldata=np.array(np.linspace(s,e,fe-fs),ndmin=2)
        for g in range(len(self.graphs)):
            yveldata=self.gData[g][fs:fe]
            yveldata=(yveldata-self.lim[g][0])/float(self.lim[g][1]-self.lim[g][0])
            yveldata[yveldata>self.lim[g][1]]=self.lim[g][1]
            yveldata[yveldata<self.lim[g][0]]=self.lim[g][0]
            yveldata=np.array((self.ga[3]-(g+1)*self.inc)
                +(self.span[g]*yveldata+self.offset[g])*self.inc,ndmin=2)
            veldata=np.concatenate((xveldata,yveldata),axis=0).T.tolist()
            self.graphs[g].setVertices(veldata)
        rct=self.gazeData.recTime # update time message
        self.tmsg.setText('Time %d:%02d:%06.3f' % (rct.hour,
                rct.minute+ (rct.second+int(self.t[self.f]/1000.0))/60,
                np.mod(rct.second+ self.t[self.f]/1000.0,60)))
        for m in self.gazeData.msgs:
            if m[0]>self.t[self.f] and m[0]<self.t[self.f]+100:
                m.append(True)
                self.msg.setText(m[2])
                self.msg.draw()
        self.frame.draw()
        self.tmsg.draw()
        Trajectory.showFrame(self,positions)
    def highlightedAgents(self): return self.gazeData.getAgent(self.t[self.f])
    
class Coder(ETReplay):
    def showFrame(self,positions):
        # draw saccades and blinks in the selection tool
        sws=np.float(self.sws); i=0; 
        s=max(self.f-sws/2.0,0);
        e= min(self.f+sws/2.0,self.gData[0].shape[0]-1)
        for k in range(len(self.sev)):
            sac=self.sev[k]
            if (sac[1]<=e and sac[1]>=s) or (sac[0]<=e and sac[0]>=s):
                ss=(max(sac[0],s)-self.f)/sws*self.ga[1]*2;
                ee=(min(sac[1],e)-self.f)/sws*self.ga[1]*2;
                self.sacrects[i].setPos(( (ee-ss)/2.0+ss,self.spar[1]))
                self.sacrects[i].setWidth(max(ee-ss,0.5))
                self.sacrects[i].setAutoDraw(True)
                self.sacrects[i].ad=k
                i+=1;
        while i<len(self.sacrects):
            self.sacrects[i].setAutoDraw(False);
            self.sacrects[i].ad=-1;i+=1;
            
        i=0;h=-1;clrs=['red','green','black']
        # draw selected blocks
        tot=float(len(self.selected))
        for selection in self.selected:
            h+=1
            for k in range(len(selection)):
                sel= selection[k]
                trigger=False
                if len(sel)==3 and self.t[int(s)]<=sel[0] and self.t[int(e)]>=sel[0] :
                    self.selrects[i].setPos(((sel[1]-self.f)/sws*self.ga[1]*2,self.spar[1]+(h-1)*self.spar[2]/tot))
                    self.selrects[i].setWidth(1);trigger=True
                elif (len(sel)>=6 and( self.t[int(s)]<=sel[3] and self.t[int(e)]>=sel[3]
                    or self.t[int(s)]<=sel[0] and self.t[int(e)]>=sel[0]
                    or self.t[int(s)]>=sel[0] and self.t[int(e)]<=sel[3])):
                    ss=(max(sel[1],s)-self.f)/sws*self.ga[1]*2
                    ee= (min(sel[4],e)-self.f)/sws*self.ga[1]*2
                    self.selrects[i].setPos(((ee-ss)/2.0 + ss,self.spar[1]+(h-1)*self.spar[2]/tot))
                    self.selrects[i].setWidth(ee-ss);trigger=True
                if trigger:
                    self.selrects[i].ad=k;self.selrects[i].h=h
                    self.selrects[i].setFillColor(clrs[h])
                    self.selrects[i].setAutoDraw(True);i+=1
        while i<len(self.selrects):
            self.selrects[i].setAutoDraw(False);
            self.selrects[i].ad=-1;i+=1;
        ETReplay.showFrame(self,positions)
        # query mouse
        mkey=self.mouse.getPressed();select=False
        if 0<sum(mkey) and self.released:
            mpos=self.mouse.getPos();issac=False
            ppos=(Q.deg2pix(mpos[0]),Q.deg2pix(mpos[1]))
            mkey=self.mouse.getPressed()
            #print mpos
            if mkey[0]>0:
                for sr in self.sacrects:
                    if sr.ad>-1 and sr.contains(ppos):
                        g=self.gazeData.getGaze()
                        if len(self.selected[0])==0 or len(self.selected[0][-1])>=6:
                            ff= self.sev[sr.ad][1]
                            gf=self.sev[sr.ad][3]
                            tt=g[gf,0]
                        else:
                            ff= self.sev[sr.ad][0]
                            gf=self.sev[sr.ad][2]
                            tt=g[gf,0]
                            #if tt>self.selected[-1][0]:
                        select=True
                if not select and  self.seltoolrect.contains(ppos):
                    ff=np.round(mpos[0]/self.ga[1]/2.0*sws)+self.f;
                    tt=self.t[min(ff,self.t.size-1)]
                    gf=np.round(ff/Q.refreshRate*self.gazeData.hz)
                    select=True
                if select:
                    if  (len(self.selected[0])==0 or len(self.selected[0][-1])>=6):
                        self.selected[0].append([tt,ff,gf])
                        self.msg.setText('Selection Open: %d'%self.selected[0][-1][0])
                    elif tt>self.selected[0][-1][0]:
                        self.selected[0][-1].extend([tt,ff,gf])
                        ags=selectAgentTRACKING(self.selected[0][-1][2], self.selected[0][-1][5],self.gazeData.events )
                        self.selected[0][-1].extend([ags,True])
                        self.msg.setText('Selection Closed: %d,%d'%(self.selected[0][-1][0], self.selected[0][-1][3]))
            else:
                for sr in self.selrects:
                    if sr.ad>-1 and  sr.contains(ppos):
                        if  sr.h==0:
                            self.selected[0].pop(sr.ad)
                            self.msg.setText('Selection Deleted')
                        elif sr.h==1:  self.selected[0].append(self.selected[1][sr.ad])
                        elif sr.h==2:  self.selected[0].append(self.selected[2][sr.ad])
            # agent selection
            for a in range(positions.shape[0]):
                dist=((positions[a,0]-mpos[0])**2+(positions[a,1]-mpos[1])**2)**0.5
                if dist<Q.agentSize/2.0: self.highlightAgent(a)
            self.released=False
        if 0==sum(mkey) and not self.released: self.released=True
        if self.save: self.saveSelection()
        
    def highlightedAgents(self): 
        for sel in self.selected[0]:
            if len(sel)>3 and sel[1]<=self.f and sel[4]>=self.f:
                return sel[6]
        return []
    def highlightAgent(self,a):
        for sel in self.selected[0]:
            if len(sel)>3 and sel[1]<=self.f and sel[4]>=self.f:
                if a in sel[6]: sel[6].remove(a)
                else: sel[6].append(a)
        
    def loadSelection(self,path=None):
        if path==None: path='track/'
        fin = open(path+'vp%03db%dtr%02d.trc'%(self.gazeData.vp,
                self.gazeData.block,self.gazeData.trial),'r')
        out=[]
        for line in fin:
            line=line.rstrip('\n')
            els= line.rsplit(' ')
            els=np.int32(els).tolist()
            out.append(els[:6])
            out[-1].append(els[6:-1])
            out[-1].append(els[-1])
        return out
    def saveSelection(self,path=None):
        """ take care that refreshrate settings remain the
            same when saving and loading """
        if path==None: path='track/'
        fout = open(path+'vp%03db%dtr%02d.trc'%(self.gazeData.vp,
                self.gazeData.block,self.gazeData.trial),'w')
        for sel in self.selected[0]:
            fout.write('%d %d %d %d %d %d'%tuple(sel[:6]))
            for el in sel[6]:
                fout.write(' %d'%el)
            fout.write(' %d'%sel[7])
            fout.write('\n')
        
        self.msg.setText('Selection Saved')
        self.save=False

class Master(Coder):
    def __init__(self,gazeData,**kwargs):
        ETReplay.__init__(self,gazeData,**kwargs)
        vp=gazeData.vp; block=gazeData.block;t=gazeData.trial
        for i in range(1,10):
            try:
                self.selected.append(self.loadSelection( 'track/coder%d/'%i))
            except: 
                break
        print self.selected
        for rect in self.selrects:
            rect.setHeight(self.spar[2]/3.0 )

def replayTrial(vp,block,trial):
    from readETData import readEyelink
    data=readEyelink(vp,block)
    trl=data[trial]
    trl.loadTrajectories()
    trl.driftCorrection()
    trl.extractTracking()
    R=Coder(gazeData=trl,phase=1,eyes=1)
    R.play(tlag=0)
    
def replayBlock(vp,block,trialStart):
    from readETData import readEyelink
    data=readEyelink(vp,block)
    for trial in range(trialStart,len(data)):
        trl=data[trial]
        trl.loadTrajectories()
        trl.driftCorrection()
        trl.extractTracking()
        R=Master(gazeData=trl,phase=1,eyes=1)
        R.play(tlag=0)
        
def codingComparison(vp=1,block=2):
    from readETData import readEyelink
    data=readEyelink(vp,block)
    for trial in range(20):
        trl=data[trial]
        trl.loadTrajectories()
        trl.driftCorrection()
        trl.extractTracking()
        R=Coder(gazeData=trl,phase=1,eyes=1)
        R.saveSelection(path='track/coder0/')
        R.wind.close()
        
    import pylab as plt
    import matplotlib as mpl
    ax=plt.gca()
    N=4; clrs=['r','g','b','k']
    for t in range(20):
        for c in range(N):
            D=np.loadtxt('track/coder%d/vp%03db%dtr%02d.trc'
                          %(c,vp,block,t))
            D=np.array(D,ndmin=2).tolist()
            for e in D:
                r=mpl.patches.Rectangle((e[0],t+c*float(N)**-1),
                    e[1]-e[0],float(N)**-1,color=clrs[c])
                ax.add_patch(r)
    plt.xlim([0,30000])
    plt.ylim([0,20])
    plt.show()
if __name__ == '__main__':
    #replayBlock(1,5,31)
    #codingComparison()
#    from readETData import readEyelink
#    vp=1;block=5
#    trial=16
#    data=readEyelink(vp,block)
#    #for trial in range(20):
#    trl=data[trial]
#    trl.loadTrajectories()
#    trl.driftCorrection()
#    trl.extractTracking()
#    R=Coder(gazeData=trl,phase=1,eyes=1)
#    R.play()

            
    from readETData import readTobii
    data=readTobii(172,0)
    for trl in data:
        R=ETReplay(gazeData=trl,phase=1,eyes=1)
        R.play(tlag=0)
