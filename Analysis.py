import numpy as np
import pylab as plt
import matplotlib as mpl
from mpl_toolkits.mplot3d import Axes3D
from scipy.ndimage.filters import gaussian_filter
from scipy.stats import nanmean

plt.close('all')
#plt.ion()
from os import getcwd
path=getcwd().rstrip('code')+'/evaluation/'
vp=1

bs=range(1,22)
sw=-400; ew=400;hz=85.0 # start, end (in ms) and sampling frequency of the saved window
fw=int(np.round((abs(sw)+ew)/1000.0*hz))
radbins=np.arange(1,15)
do=1 # 0 - si; 1- ti

def plotSearchInfo(plot=True):
    if do==0: D=np.load(path+'SIvp%03d.npy'%(vp))
    elif do==1:
        ti=np.load(path+'TIvp%03d.npy'%vp)
        ti=ti[ti[:,14]==0,:]
        ti=ti[ti[:,11]-ti[:,4]>=0,:]
        D=ti
    if plot:
        #plt.close('all')
        plt.figure()
        plt.plot(D[:,6],D[:,7],'.k')
        plt.title('Target positions')
        ax=plt.gca()
        ax.set_aspect(1)

        plt.figure()
        plt.plot(D[:,2],D[:,3],'.k')
        plt.title('Disengagement positions')
        ax=plt.gca()
        ax.set_aspect(1)

        plt.figure()
        reloc=np.sqrt(np.sum(np.power(D[:,[6,7]]-D[:,[2,3]],2),axis=1))
        plt.title('Distance')
        plt.hist(reloc,50)
        plt.xlim([0,20])

        plt.figure()
        dur = D[:,5]-D[:,1]
        plt.hist(dur,50)
        plt.title('Duration')
        plt.xlim([0,250])

        plt.figure()
        vel=reloc/dur
        plt.hist(vel[~np.isnan(vel)]*1000,50)
        plt.title('Velocity')
        plt.xlim([0,200])
    return D


def loadData():
    si=plotSearchInfo(plot=False)
    inpath=getcwd().rstrip('code')+'input/'
    sf=np.int32(np.round((si[:,1]+sw)/1000.0*hz))
    ef=sf+fw
    if do==0: valid= np.logical_and(si[:,1]+sw>=0, si[:,1]+ew <= si[:,-3])
    else: valid= np.logical_and(si[:,1]+sw>=0, si[:,1]+ew <= si[:,12])
    print 'proportion of utilized samples is', valid.mean()
    D=np.zeros((valid.sum(),fw,14,2))*np.nan
    DG=np.zeros((valid.sum(),fw,14,2))*np.nan
    DT=np.zeros((valid.sum(),fw,14,2))*np.nan
    DP=np.zeros((valid.sum(),fw,14,2))*np.nan
    DA=np.zeros((valid.sum(),fw,14,2))*np.nan
    k=0; lastt=-1;
    rt=np.random.permutation(valid.nonzero()[0])
    for h in range(si.shape[0]):
        if not valid[h]: continue
        if si[h,-1]!=lastt:
            order = np.load(inpath+'vp%03d/ordervp%03db%d.npy'%(vp,vp,si[h,-2]))
            traj=np.load(inpath+'vp%03d/vp%03db%dtrial%03d.npy'%(vp,vp,si[h,-2],order[si[h,-1]]) )
        D[k,:,:,:]=traj[sf[h]:ef[h],:,:2]
        DT[k,:,:,:]=traj[sf[rt[k]]:ef[rt[k]],:,:2]
        k+=1; lastt=si[h,-2]
    rp=np.random.permutation(valid.nonzero()[0])
    #sel=si[:,8]>0#np.logical_not(np.all(np.all(np.all(np.isnan(D[:,:14]),3),2),1))
    #DG=DG[sel,:,:,:]
    for a in range(14):
        for f in range(fw):
            for q in range(2):
                DG[:,f,a,q]= D[:,f,a,q] - si[valid,6+q]
                DT[:,f,a,q]-= si[rt,6+q]
                DA[:,f,a,q]= D[:,f,a,q] - D[:,D.shape[1]/2,2,q]
                DP[:,f,a,q]= D[:,f,a,q] - si[rp,6+q]
                
                
    return [DG,DP,DA,DT]

def agentDensity(D):
    #np.random.seed(1234)
    shape=D[0].shape
    #plt.close('all');
    I=[]
    bnR=np.arange(0,30,0.5)
    bnS=np.diff(np.pi*bnR**2)
    bnd= bnR+(bnR[1]-bnR[0])/2.0;bnd=bnd[:-1]
    for i in range(len(D)): I.append(np.zeros((bnS.size,shape[1])))
    plot=True
    g=1;figs=range(1,100);fig1=figs.pop(0);fig2=figs.pop(0)
    r=np.random.permutation(shape[0])
    n=shape[0]*shape[2]
    for f in range(0,shape[1]):
        H=[]
        for q in range(len(D)):
            H.append(D[q][:,f,:,:].reshape([n,1,1,2]).squeeze())
        if plot:
            if g>12: fig1=figs.pop(0); fig2=figs.pop(0); g=1
            plt.figure(fig1)
            plt.subplot(3,4,g)
            plt.title('Frame %.1f'%(f*1000/hz+sw))
            bn=np.linspace(-20,20,41)
            b1,c,d=np.histogram2d(H[0][:,0],H[0][:,1],bins=[bn,bn])
            b2,c,d=np.histogram2d(H[1][:,0],H[1][:,1],bins=[bn,bn])
            plt.imshow(b1-b2, extent=[-20,20,-20,20],origin='lower',
                       interpolation='nearest')#,vmin=-140,vmax=40)
            plt.set_cmap('hot')
            plt.colorbar()
            plt.figure(fig2)
            plt.subplot(3,4,g)
            plt.title('Frame %.1f'%(f*1000/hz+sw))
            g+=1
        for q in range(len(D)): 
            a,b=np.histogram(np.sqrt(np.power(H[q],2).sum(axis=1)),bins=bnR)
            I[q][:,f]=a/np.float32(shape[0]*bnS)*a.size
            if q==6:
                print (a/float(shape[0])*a.size).mean(), bnS.sum(),26*26,I[q][:,f].sum()
                bla
            #if q==2: I[q][0,f]=np.nan
            if plot: plt.plot(bnd,I[q][:,f])
##            blb=np.copy(bnS);blb[0]=0
##            if plot:
##               plt.plot(bnd,a/blb/n*(bnR.size-1))
        if plot:
            #plt.ylim([0,0.5])
            plt.xlabel('Distance from Saccade Target Location')
            plt.ylabel('Agent Density [a per deg^2]') #[# agents per deg^2]
            if g==2:plt.legend(['rand pos','gaze','rand ag','rand time'])
    plt.figure()
    if plot:
        for q in I:
            plt.imshow(q,extent=[sw,ew,bnR[0],bnR[-1]],aspect=10,origin='lower')
            plt.ylabel('radial distance from sac target')
            plt.xlabel('time from sac onset')
            plt.colorbar();plt.set_cmap('hot')
            plt.figure()
    for q in I: plt.plot(bnd,q.mean(1))
    plt.xlabel('radial distance')
    plt.ylabel('Agent Density [a per deg^2]')
    plt.legend(['gaze','rand pos','rand agent','rand time'])
    plt.figure()
    x=np.linspace(sw,ew,I[0].shape[1])
    hhh=10
    for q in I: plt.plot(x,nanmean(q[:hhh,:],0))
    plt.xlabel('time')
    plt.title('Radius=5 deg')
    plt.ylabel('Agent Density [a per deg^2]')
    plt.xlabel('time to saccade onset')
    plt.legend(['gaze','rand pos','rand agent','rand time'],loc=2)
    

def dirChanges(D):
    #plt.close('all');
    P=[];J=[];K=[];nK=[]
    shape=D[0].shape
    bn=np.arange(0,20,0.5)
    d= bn+(bn[1]-bn[0])/2.0;d=d[:-1]
    c=np.diff(np.pi*bn**2)
    for q in range(len(D)):
        J.append(np.zeros((shape[0],shape[1]-2,shape[2])))
        P.append(np.zeros((shape[0],shape[1]-2,shape[2])))
        K.append(np.zeros((d.size,shape[1]-2,shape[2])))
        nK.append(np.zeros((d.size,shape[1]-2,shape[2])))
    tol=0.0001
    for a in range(shape[2]):
        for q in range(len(D)):
            for f in range(1,shape[1]-1):
                P[q][:,f-1,a]=np.sqrt(np.power(D[q][:,f,a,:],2).sum(1))
            J[q][:,:,a]= np.logical_or(np.abs(np.diff(D[q][:,:,a,1],2))>tol,
                np.abs(np.diff(D[q][:,:,a,0],2))>tol)
    for i in range(d.size):
        for f in range(shape[1]-2):
            for a in range(shape[2]):
                sel=[]
                for q in range(len(D)):
                    if i==len(bn)-1:
                        sel.append(P[q][:,f,a]>bn[i])
                    else:
                        sel.append(np.logical_and(P[q][:,f,a]>bn[i],P[q][:,f,a]<bn[i+1]))
                    K[q][i,f,a]=np.sum(J[q][sel[q],f,a],axis=0)*hz
                    nK[q][i,f,a]=np.sum(sel[q])
        print i
    sig=[0.5,0.5]
    for q in range(len(D)):
        plt.imshow(np.nansum(K[q],2)/np.sum(nK[q],2),origin='lower',extent=[sw,ew,bn[0],bn[-1]],aspect=20,cmap='hot',vmax=11,vmin=2)     
        plt.colorbar()
        plt.figure()
    for q in range(len(D)):
        plt.plot(d,np.nansum(np.nansum(K[q],2),1)/ nK[q].sum(2).sum(1))
    plt.legend(['gaze','rand pos','rand ag','rand time'])
    plt.ylabel('Direction Changes per Second')
    plt.xlabel('Radial Distance in Deg')
    plt.figure()
    x=np.linspace(sw,ew,K[0].shape[1])
    kk=10
    for q in range(len(D)):
        plt.plot(x,np.nansum(np.nansum(K[q][:kk,:,:],2),0)/ nK[q][:kk,:,:].sum(2).sum(0))
    plt.legend(['gaze','rand pos','rand ag','rand time'])
    plt.ylabel('Direction Changes per Second')
    plt.xlabel('Time, Saccade Onset at t=0')
    plt.title('Radius = 10 deg')
    #return K,nK

def extractSaliency():
    from ezvisiontools import Mraw
    si=plotSearchInfo(plot=False)
    inpath=getcwd().rstrip('code')+'input/'
    sf=np.int32(np.round((si[:,1]+sw)/1000.0*hz))
    ef=sf+fw
    valid= np.logical_and(si[:,1]+sw>=0, si[:,1]+ew <= si[:,-3])
    si=si[valid,:]
    sf=sf[valid]
    ef=ef[valid]
    lastt=-1;dim=64;k=0
    gridG=np.zeros((fw,dim,dim));radG=np.zeros((fw,radbins.size))
    gridT=np.zeros((fw,dim,dim));radT=np.zeros((fw,radbins.size))
    gridA=np.zeros((fw,dim,dim));radA=np.zeros((fw,radbins.size))
    gridP=np.zeros((fw,dim,dim));radP=np.zeros((fw,radbins.size))
    rt=np.random.permutation(si.shape[0])
    rp=np.random.permutation(si.shape[0])
    for h in range(si.shape[0]):
        if si[h,-1]!=lastt:
            order = np.load(inpath+'vp%03d/ordervp%03db%d.npy'%(vp,vp,si[h,-2]))
            traj=np.load(inpath+'vp%03d/vp%03db%dtrial%03d.npy'%(vp,vp,si[h,-2],order[si[h,-1]]))
            try: vid=Mraw(getcwd()+'/saliency/output/vp%03d/vp%03db%dtrial%03dCOmotion-.%dx%d.mgrey'%(vp,vp,int(si[h,-2]),order[si[h,-1]],dim,dim))
            except:
                continue
        temp1,temp2=vid.computeSaliency(si[h,[6,7]],[sf[h],ef[h]],rdb=radbins)
        gridG+=temp1; radG+=temp2.T; lastt=si[h,-2];
        temp1,temp2=vid.computeSaliency(si[rt[h],[6,7]],[sf[rt[h]],ef[rt[h]]],rdb=radbins)
        gridT+=temp1; radT+=temp2.T;
        temp1,temp2=vid.computeSaliency(traj[sf[h]+fw/2,2,:2],[sf[h],ef[h]],rdb=radbins)
        gridA+=temp1; radA+=temp2.T;
        temp1,temp2=vid.computeSaliency(si[rp[h],[6,7]],[sf[h],ef[h]],rdb=radbins)
        gridP+=temp1; radP+=temp2.T;k+=1
        print k
        

    gridG/=float(k);radG/=float(k);gridT/=float(k);radT/=float(k)
    gridP/=float(k);radP/=float(k);gridA/=float(k);radA/=float(k)
    np.save(getcwd()+'/saliency/vp%03dMgridG.npy'%vp,gridG)
    np.save(getcwd()+'/saliency/vp%03dMradG.npy'%vp,radG)
    np.save(getcwd()+'/saliency/vp%03dMgridT.npy'%vp,gridT)
    np.save(getcwd()+'/saliency/vp%03dMradT.npy'%vp,radT)
    np.save(getcwd()+'/saliency/vp%03dMgridA.npy'%vp,gridA)
    np.save(getcwd()+'/saliency/vp%03dMradA.npy'%vp,radA)
    np.save(getcwd()+'/saliency/vp%03dMgridP.npy'%vp,gridP)
    np.save(getcwd()+'/saliency/vp%03dMradP.npy'%vp,radP)

def plotSaliency():
    K=[];I=[]
    for s in ['G','T','A','P']:
        K.append(np.load(getcwd()+'/saliency/vp%03dMgrid%s.npy'%(vp,s)))
        I.append(np.load(getcwd()+'/saliency/vp%03dMrad%s.npy'%(vp,s)).T)

    plt.figure();plot=False
    if plot:
        for q in I:
            plt.imshow(q,extent=[sw,ew,radbins[0],radbins[-1]],
                aspect=30,origin='lower',vmin=0.008, vmax=0.021)
            plt.ylabel('radial distance from sac target')
            plt.xlabel('time from sac onset')
            plt.title('saliency')
            plt.colorbar();plt.set_cmap('hot')
            plt.figure()
    for q in I: plt.plot(radbins,q.mean(1))
    plt.xlabel('radial distance')
    plt.ylabel('Average Saliency [0,1]')
    plt.legend(['gaze','rand time','rand agent','rand pos'])
    plt.figure()
    x=np.linspace(sw,ew,I[0].shape[1])
    hhh=3
    for q in I: plt.plot(x,nanmean(q[:hhh,:],0))
    plt.xlabel('time')
    plt.title('Radius=%d deg'%hhh)
    plt.ylabel('Average Saliency [0,1]')
    plt.xlabel('time to saccade onset')
    plt.legend(['gaze','rand time','rand agent','rand pos'],loc=2)

    plt.show()

### different method for extracting radial density, gives similar results
##H,C,G,bn=agentDensity(D,si)
##def radialHist(M,bn,nn):
##    from scipy.interpolate import interp1d
##    b,c,d=np.histogram2d(M[:,0],M[:,1],bins=[bn,bn])
##    # find bin center
##    d= bn+(bn[1]-bn[0])/2.0
##    d=d[:-1]
##    # get unique data points
##    xa,xb=np.meshgrid(d,d)
##    x=np.sqrt(xa**2+xb**2)
##    x=np.reshape(x,x.size)
##    y=np.reshape(b,b.size)
##    nx=np.unique(x)
##    ny=[]
##    for k in nx.tolist():
##        ny.append(y[x==k].mean())
##    ny=np.array(ny)
##    # interpolate
##    f=interp1d(nx,ny)
##    plt.plot(nn,f(nn))
##
##plt.figure()
##radialHist(H,bn,range(1,26))
##radialHist(C,bn,range(1,26))
##radialHist(G,bn,range(1,26))
##plt.legend(['gaze','rand pos','rand ag'])




def pcaMotionSingleAgent(D,ag=3,plot=False):
    for q in range(len(D)):
        E=D[q]
        F=np.zeros((E.shape[0],E.shape[3]*E.shape[1]))
        for k in range(E.shape[0]):
            F[k,:]= E[k,:,ag,:].reshape([F.shape[1],1]).squeeze()
        pcs,score,lat=princomp(F)
        plt.figure(1)
        plt.plot(lat)
        plt.legend(['gaze','rand pos','rand ag','rand time'])
        plt.figure(2)
        for i in range(6):
            plt.subplot(2,3,i+1)
            b=pcs[:,i].reshape([E.shape[1],E.shape[3]])
            plt.plot(b[:,0],b[:,1]);
        plt.legend(['gaze','rand pos','rand ag','rand time'])
    if plot:
        # items
        plt.figure()
        plt.plot(score[0,:],score[1,:],'.');plt.gca().set_aspect(1);
        plt.figure()
        plt.plot(score[2,:],score[3,:],'.');plt.gca().set_aspect(1);
        plt.figure()
        plt.plot(score[4,:],score[5,:],'.');plt.gca().set_aspect(1);
        # traj reconstraction with help of first few components
        for k in range(10):
            res=0
            for i in range(6): res+=pcs[:,i]*score[i,k]
            res=res.reshape([E.shape[1],E.shape[3]])
            plt.figure()
            plt.plot(E[k,:,0,0],E[k,:,0,1]);
            plt.plot(res[:,0],res[:,1]);

def pcaMotionMultiAgent(D):
    q=1
    E=D[q]
##    F=np.zeros((E.shape[0],E.shape[3]*E.shape[1]*E.shape[2]))
##    for k in range(E.shape[0]):
##        B=np.copy(E[k,:,:,:])
##        r=np.random.permutation(range(E.shape[2]))
##        #B=B[:,r,:]
##        F[k,:]= B.reshape([F.shape[1],1]).squeeze()
##    pcs,score,lat=princomp(F)
##    np.save('pcs%d'%q,pcs)
##    np.save('lat%d'%q,lat)
##    np.save('score%d'%q,score)
    
    pcs=np.load('pcs%d.npy'%q)
    score=np.load('score%d.npy'%q)
    lat=np.load('lat%d.npy'%q)
    plt.figure(1)
    plt.plot(lat)
    plt.xlim([0,30])
    #plt.legend(['gaze','rand pos','rand ag','rand time'])
    plt.figure(2)
    for i in range(30):
        plt.subplot(5,6,i+1)
        b=pcs[:,i].reshape([E.shape[1],E.shape[2],E.shape[3]])
        plotTraj(b);

def EMpca(X,p):
    ''' data is a matrix holding the input data
        each column of data is one data vector
        NB: mean will be subtracted and discarded
        p    is # of principal components to find
    '''
    
    K,N=X.shape
    for k in range(K): X[k,:]-= X[k,:].mean()
    X= np.matrix(X)
    W= np.matrix(np.random.rand(K,p))
    tol=1e-8;error=np.inf; last=np.inf
    while not abs(last-error)<error*tol:
        Z,bla,blaa,blaaa=np.linalg.lstsq(W.T*W, W.T*X)#Z = (W'*W)\(W'*X);
        b=Z*Z.T;a=X*Z.T
        try: W=np.linalg.solve(a,b)
        except: W,bla,blaa,blaaa=np.linalg.lstsq(b.T,a.T);W=W.T
        last =error
        E=X-W*Z
        error= np.power(E,2).sum()/N
        print abs(last-error)/error
    W,R=np.linalg.qr(W)
    Z=W.T*X
    #for k in range(p): Z[k,:]-= Z[k,:].mean()
    A,V=np.linalg.eig(Z*Z.T)
    idx=np.argsort(A)[::-1]
    V=np.matrix(V[:,idx]).T
    V=W*V
    A=A[idx]
    return V,A
    
    
    
def plotTraj(traj):
    ax=plt.gca()
    clr=['g','r','k']
    for a in range(traj.shape[1]):
        x=traj[:,a,0];y=traj[:,a,1]
        plt.plot(x,y,clr[min(a,2)]);
        #arr=plt.arrow(x[-2], y[-2],x[-1]-x[-2],y[-1]-y[-2],width=0.2,fc='k')
        plt.plot(x[-1],y[-1],'.'+clr[min(a,2)])
        #ax.add_patch(arr)
        midf=traj.shape[0]/2
        #arr=plt.arrow(x[midf], y[midf],x[midf+1]-x[midf],y[midf+1]-y[midf],width=0.1,fc='g')
        #ax.add_patch(arr)

    #rect=plt.Rectangle([-5,-5],10,10,fc='white')
    #ax.add_patch(rect)
    plt.plot(0,0,'ob')
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.set_xticks([])
    ax.set_yticks([])
    #plt.xlim([-20,20])
    #plt.ylim([-20,20])
    ax.set_aspect('equal')


   

if __name__ == '__main__':
##    from matplotlib.mlab import PCA
##    from test import princomp
##    D=[]
##    for i in range(4): D.append(np.load('D%d.npy'%i))
##    si=plotSearchInfo(False)
##
##    q=1
##    E=D[q]
##    F=[]
##    for q in range(2):
##        F.append(np.zeros((E.shape[0],E.shape[3]*E.shape[1]*E.shape[2])))
##        for k in range(E.shape[0]):
##            B=np.copy(E[k,:,:,:])
##            F[q][k,:]= B.reshape([F[q].shape[1],1]).squeeze()
##    x=np.concatenate(F,axis=0)
##    x=np.concatenate([-np.ones((x.shape[0],1)), x],axis=1)
##    y=np.zeros((F[q].shape[0]*2))
##    y[:F[q].shape[0]]=1
##    del D, E, F

    #lr.checkCorrectness(x,y)
    #pcaMotionMultiAgent(D)
    #pcaMotionSingleAgent(D)
    do=0
    D=loadData()
    dirChanges(D)
    do=1
    D=loadData()
    dirChanges(D)
    plt.show()
    #dirChanges(D)


    
    
    
    

    




