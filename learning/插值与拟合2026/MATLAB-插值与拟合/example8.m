tdata=100:100:1000;
cdata=0.001*[4.54 4.99 5.35 5.65 5.90 6.10 6.26 6.39 6.50 6.59];
x0=[0.1 0.1 0.1];
x=lsqcurvefit('fun1',x0,tdata,cdata);
f=fun1(x,tdata)
c=f-cdata;
plot(tdata,cdata,'*',tdata,f);
betafit=nlinfit(tdata,cdata,'fun1',x0);
[betafit1,r,J]=nlinfit(tdata,cdata,'fun1',x0);