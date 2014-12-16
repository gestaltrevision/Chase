import numpy as np
import pylab as plt
from scipy import stats
from matustools.matusplotlib import *
import os
from matustools.matusplotlib import ndarray2gif,plotGifGrid,str2img

FIG=(('behdata.png',('Detection Time in Seconds','Probability' ),
                     ('Subject','Mean Detection Time'),
                     ('Subject',),
                     ('','Detection Rate'),()),
     ('bdtime.png',('Trial','Proportion Correct',['1','2','3','4'])),
     ('analysis/agdens',('Radial Distance','Agent Density',['S1','S2','S3','S4','RT']),
      ('Time to Saccade Onset','Agent Density'),
      ('Radial Distance','Direction Changes'),
      ('Time to Saccade Onset','Direction Changes'),
      ('Radial Distance', 'Light Contrast Saliency'),
      ('Radial Distance', 'Motion Saliency'),
      ('Time to Saccade Onset', 'Light Contrast Saliency'),
      ('Time to Saccade Onset', 'Motion Saliency')),
     ('',())
     )

inpath = os.getcwd().rstrip('code')+'evaluation'+os.path.sep
figpath = os.getcwd().rstrip('code')+'figures'+os.path.sep
def plotBehData():
    from matustools.matustats import lognorm
    rtmc=np.load(inpath+'rtmc.npy')
    rejs=np.load(inpath+'rejs.npy')
    rts=np.load(inpath+'rts.npy')
    acc=np.load(inpath+'acc.npy')
    figure(size=1,aspect=1.4)
    subplot(3,1,1)
    vp=0
    d=rts[vp,rejs[vp,:]==1]
    d=d[d>0]
    x=np.linspace(1,30,30)
    hist(d,bins=x,normed=True)
    plt.plot(x-0.5,lognorm(mu=rtmc[vp,-2,:].mean(),
                sigma=rtmc[vp,-1,:].mean()).pdf(x-0.5),'k')
    plt.xlabel(FIG[0][1][0])
    plt.ylabel(FIG[0][1][1])
    subplot_annotate(loc='ne',nr=0)
    #plt.subplot(2,2,i+1);i+=1
    for k in range(4):
        subplot(3,2,[3,4,5,6][k])
        if k<2: 
            plt.ylim([6,20]);
            plt.xlabel(FIG[0][2+k][0])
        else:plt.gca().set_xticklabels([])
        if k==0: plt.ylabel(FIG[0][1+k][1])
        elif k>1: 
            plt.ylim([0.75,1])
        if k==2:plt.ylabel(FIG[0][2+k][1])
        if k%2==1: plt.gca().set_yticklabels([])
        
        errorbar(rtmc[:,k,:].T,x=range(1,5))
        subplot_annotate(loc='ne',nr=k+1)
    plt.subplots_adjust(wspace=0.01,hspace=-0.2)
    plt.savefig(figpath+FIG[0][0],dpi=400,bbox_inches='tight')

    figure(aspect=0.6)
    for vp in range(4):
        sel= ~np.isnan(rts[vp,:])
        d=np.int32(acc[vp,sel]==1)
        d=np.reshape(d,(d.size/10.,10))
        y=d.mean(1)
        x=np.arange(y.size)*10
        plt.plot(x+(vp-1.5)*1,y+(vp-1.5)*0.01,'+',ms=5,mew=1)
    plt.ylim([0.2,1.05])
    plt.gca().set_xticks(range(0,y.size*10,40))
    plt.grid(True,axis='x')
    plt.xlim([-4,250])
    plt.xlabel(FIG[1][1][0])
    plt.ylabel(FIG[1][1][1])
    leg=plt.legend(FIG[1][1][2],loc=4,numpoints=1,frameon=True,
                   ncol=1,fontsize='small',labelspacing=0)
    box=leg.get_frame()
    box.set_linewidth(0.)
    box.set_facecolor([0.9]*3)
    plt.savefig(figpath+FIG[1][0],dpi=400,bbox_inches='tight')
    plt.close('all')


def plotAnalysis(event=-1):
    lim=[[0.25,2.5],[0.37,2.5]]
    for vp in range(1,5):
        plt.figure(0)
        if event>-1: sw=-400; ew=400
        else: sw=-800; ew=0
        hz=85.0 # start, end (in ms) and sampling frequency of the saved window
        fw=int(np.round((abs(sw)+ew)/1000.0*hz))
        bnR=np.arange(0,30,0.5)
        bnS=np.diff(np.pi*bnR**2)
        bnd= bnR+(bnR[1]-bnR[0])/2.0;bnd=bnd[:-1]
        path=inpath+'vp%03d/'%vp
        subplot(4,2,1)
        I=np.load(path+'E%d/agdens.npy'%event)
        I/=float(bnR.size)
        I*=100. # density in nr agents per 100 deg^2
        m=I.shape[2]/2
        plt.plot(bnd,I[0,:,m,0])
        if vp==4:
            #plt.plot(bnd,I[2,:,m,0])
            # show histogram
            x=np.concatenate([bnd,bnd[::-1]])
            ci=np.concatenate([I[2,:,m,2],I[2,:,m,1][::-1]])
            plt.gca().add_patch(plt.Polygon(np.array([x,ci]).T,
                        alpha=0.2,fill=True,fc='red',ec='red'))
        plt.xlabel(FIG[2][1][0])
        plt.ylabel(FIG[2][1][1])
        plt.legend(FIG[2][1][2],loc=1,fontsize=7)
        plt.grid();plt.ylim([0,lim[event][0]]);
        plt.xlim([0,14])

        subplot(4,2,2)
        plt.grid()
        x=np.linspace(sw,ew,I[0].shape[1])/1000.
        x=np.reshape(x,[x.size/2,2]).mean(1)
        hhh=0
        plt.plot(x,np.reshape(I[0,hhh,:,0],[x.size,2]).mean(1))
        if vp==4: plt.plot(x,np.reshape(I[2,hhh,:,0],[x.size,2]).mean(1))
        plt.ylim([0,lim[event][0]]);
        plt.xlim([-0.4,0.4])
        #plt.title('Radius=5 deg')
        plt.xlabel(FIG[2][2][0])
        plt.ylabel(FIG[2][2][1])#[a per deg^2]
        

        #direction change
        K=np.load(path+'E%d/dcK.npy'%event)
        nK=np.load(path+'E%d/dcnK.npy'%event)
        bn=np.arange(0,20,0.5)
        d= bn+(bn[1]-bn[0])/2.0;d=d[:-1]
        c=np.diff(np.pi*bn**2)
        # this code fragment shows the interaction
        #plt.figure(1)
        #plt.subplot(2,2,vp)
        #plt.imshow(np.nansum(K[0],2)/np.sum(nK[0],2),origin='lower',extent=[sw,ew,bn[0],bn[-1]],aspect=20,cmap='hot',vmax=11,vmin=2)     
        #plt.colorbar()
        ################
        plt.figure(0)
        subplot(4,2,3)
        hz=85.0
        mm=K[0].shape[1]/2
        plt.plot(d,np.nansum(K[0][:,mm,:],1)/ nK[0][:,mm,:].sum(1)*hz)
        if vp==4:# confidence band assuming iid binomial
            p=np.nansum(K[2][:,mm,:],1)/ nK[2][:,mm,:].sum(1)
            ci=1.96*np.sqrt(p*(1-p)/nK[2][:,mm,:].sum(1))
            l=(p-ci)*hz;h=(p+ci)*hz
            x=np.concatenate([d,d[::-1]])
            ci=np.concatenate([h,l[::-1]])
            plt.gca().add_patch(plt.Polygon(np.array([x,ci]).T,
                        alpha=0.2,fill=True,fc='red',ec='white'))
        plt.xlabel(FIG[2][3][0])  
        plt.ylabel(FIG[2][3][1])
        
        plt.xlim([0,14]);plt.grid();plt.ylim([0,12])
        subplot(4,2,4)
        x=np.linspace(sw,ew,K[0].shape[1])/1000.
        ss=2
        x=np.reshape(x,[x.size/ss,ss]).mean(1)
        kk=0
        y=np.nansum(K[0][kk,:,:],1)/ nK[0][kk,:,:].sum(1)*hz
        plt.plot(x,np.reshape(y,[x.size,ss]).mean(1))
        if vp==4:
            #plt.plot(x,np.nansum(K[2][kk,:,:],1)/ nK[2][kk,:,:].sum(1))
            p=np.nansum(K[2][kk,:,:],1)/nK[2][kk,:,:].sum(1)
            ci=1.96*np.sqrt(p*(1-p)/nK[2][kk,:,:].sum(1))
            l=(p-ci)*hz;h=(p+ci)*hz
            l=np.reshape(l,[x.size,ss]).mean(1);h=np.reshape(h,[x.size,ss]).mean(1)
            x=np.concatenate([x,x[::-1]])
            ci=np.concatenate([h,l[::-1]])
            
            plt.gca().add_patch(plt.Polygon(np.array([x,ci]).T,
                        alpha=0.2,fill=True,fc='red',ec='white'))
        plt.xlabel(FIG[2][4][0])  
        plt.ylabel(FIG[2][4][1])
        plt.xlim([-0.4,0.4])
        plt.ylim([0,12])
        #plt.title('Radius = 10 deg')
        plt.grid()
        
        hh=-1
        for chan in ['SOintensity','COmotion']:
            hh+=1
            K=np.load(path+'E%d/grd%s.npy'%(event,chan))
            I=np.load(path+'E%d/rad%s.npy'%(event,chan)).T
            if vp==4:IR=np.load(path+'E%d/radT%s.npy'%(event,chan)).T
                
            subplot(4,2,5+2*hh)
            plt.plot(np.arange(1,15),I[:,I.shape[1]/2])
            if vp==4: plt.plot(np.arange(1,15),IR[:,IR.shape[1]/2])
            plt.xlabel(FIG[2][5+hh][0])  
            plt.ylabel(FIG[2][5+hh][1])
            plt.ylim([0.008,lim[event][1]])
            
            plt.grid();plt.xlim([0,14])
            subplot(4,2,6+2*hh)
            x=np.linspace(sw,ew,I.shape[1])/1000.
            hhh=3
            #plt.plot(x,np.nanmean(I[:hhh,:],0))
            plt.plot(x,I[0,:])
            if vp==4: plt.plot(x,IR[0,:])
            plt.xlabel(FIG[2][7+hh][0])
            plt.ylabel(FIG[2][7+hh][1])
            plt.ylim([0.008,lim[event][1]])
            plt.xlim([-0.4,0.4])
            plt.grid()
        #plt.legend(['gaze','rand time','rand agent','rand pos'],loc=2)
        #plt.show()
    plt.savefig(figpath+FIG[2][0]+'E%d.png'%event)
    plt.close('all')

# PF pca

def _getPC(pf,h):
    if pf.shape[0]!=64:pf=pf[:,h].reshape((64,64,68))
    pf-= np.min(pf)
    pf/= np.max(pf)
    return np.rollaxis(pf.squeeze(),1).T

def plotCoeff(event,rows=8,cols=5):
    panels=[]
    for vp in range(1,5):
        path=inpath+'vp%03d/E%d/'%(vp,event)
        coeff=np.load(path+'X/coeff.npy')
        offset=8 # nr pixels for border padding
        R=np.ones((69,(64+offset)*rows,(64+offset)*cols),dtype=np.float32)
        for h in range(coeff.shape[1]):
            if h>=rows*cols:continue
            c= h%cols;r= h/cols
            s=((offset+64)*r+offset/2,(offset+64)*c+offset/2)
            pc= _getPC(coeff,h)
            if pc.mean()>=0.4: R[1:,s[0]:s[0]+64,s[1]:s[1]+64]= 1-pc
            else: R[1:,s[0]:s[0]+64,s[1]:s[1]+64]= pc
        panels.append(np.copy(R))
    pad=20
    a,b,c=R.shape
    T=np.ones((a,(b+pad)*2,c*2+pad))
    T[:,pad:(b+pad),:c]=panels[0]
    T[:,pad:(b+pad),(c+pad):(2*c+pad)]=panels[1]
    T[:,(b+2*pad):(2*b+2*pad),:c]=panels[2]
    T[:,(b+2*pad):(2*b+2*pad),(c+pad):(2*c+pad)]=panels[3]
    labels=[]
    for i in range(4): labels.append(str2img('ABCD'[i],20))
    T[:,:labels[0].shape[0],:labels[0].shape[1]]-=labels[0]
    T[:,:labels[1].shape[0],(c+pad):(c+pad+labels[1].shape[1])]-=labels[1]
    T[:,(b+pad):(b+pad+labels[2].shape[0]),:labels[2].shape[1]]-=labels[2]
    T[:,(b+pad):(b+pad+labels[3].shape[0]),
      (c+pad):(c+pad+labels[3].shape[1])]-=labels[3]
    ndarray2gif(figpath+'PercFields/pcE%d'%(event),
                T,duration=0.1,plottime=True,snapshot=True)
def plotLatent():
    for ev in range(2):
        for vp in range(1,5):
            path=inpath+'vp%03d/E%d/X/'%(vp,ev)
            plt.subplot(1,2,ev+1)
            var=np.load(path+'latent.npy')
            plt.plot(range(1,21),var[:20])
            plt.xlabel('Principal components');plt.xlim([0,21])
            plt.ylabel('Proportion of explained variance')
            plt.grid(b=False,axis='x');plt.ylim([0,0.11])
            plt.gca().set_yticks(np.arange(0,0.12,0.01))
    plt.legend(range(1,5));print var.sum(),var[:20].sum(),var[:4].sum()
    plt.savefig(figpath+'PercFields/pcaVar.png',
                dpi=400,bbox_inches='tight')


def plotScore(vp,event,pcs=5,scs=3):
    path=inpath+'vp%03d/E%d/'%(vp,event)
    score=np.load(path+'X/score.npy')
    coeff=np.load(path+'X/coeff.npy')
    offset=18 # nr pixels for border padding
    rows=scs*2+1; cols=pcs
    R=np.ones((69,(64+offset)*rows,(64+offset)*cols),dtype=np.float32)
    from pickle import load
    f=open(path+'PF.pars','r');dat=load(f);f.close()
    bd=score.shape[0]/dat['N']
    for h in range(pcs):
        s=((offset+64)*scs+offset/2,(offset+64)*h+offset/2)
        pc=_getPC(coeff,h)
        print pc.mean()
        if pc.mean()>=0.4:
            R[1:,s[0]:s[0]+64,s[1]:s[1]+64]=1-pc
            ns=np.argsort(-score[:,h])[range(-scs,0)+range(scs)]
        else:
            R[1:,s[0]:s[0]+64,s[1]:s[1]+64]=pc
            ns=np.argsort(score[:,h])[range(-scs,0)+range(scs)]
        for i in range(len(ns)):
            pf=np.load(path+'PF/PF%03d.npy'%(ns[i]/bd))[ns[i]%bd,:,:,0,:]
            s=((offset+64)*(i+int(i>=scs))+offset/2,(offset+64)*h+offset/2)
            #print h,i,ns[i],ns[i]/bd,ns[i]%bd, s
            R[1:,s[0]:s[0]+64,s[1]:s[1]+64]= _getPC(np.float32(pf),h)
    
    ndarray2gif(figpath+'PercFields/scoreVp%de%d'%(vp,event),
                np.uint8(R*255),duration=0.1,plottime=False)


if __name__=='__main__':
    #plotBehData()
    #plotAnalysis(event=0)
    #plotAnalysis(event=1)
    for ev in [0,1,2]:
        for vp in range(1,5):
            plotCoeff(ev,rows=4)
            plotScore(vp,ev,pcs=5)
    #plotLatent()

##    plt.figure()
##    radbins=np.arange(1,15)
##    plt.imshow(I,extent=[sw,ew,radbins[0],radbins[-1]],
##        aspect=30,origin='lower',vmin=0.008, vmax=0.021)
##    plt.ylabel('radial distance from sac target')
##    plt.xlabel('time from sac onset')
##    plt.title('saliency')
##    plt.grid()
##    plt.colorbar();#plt.set_cmap('hot')
##    plt.show()
    
##    plt.figure()
##    plt.imshow(K[34,:,:]);plt.grid()
##    plt.show()
