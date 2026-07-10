 x=0:0.3:3;
 y=(x.^2-4*x+2).*sin(x);
 x0=0:0.01:3;
 y_spline=interp1(x,y,x0,'spline');
 y_pchip=interp1(x,y,x0,'pchip');
 plot(x,y,'o');
 hold on
 plot(x0,y_spline,'r');
 hold on
 plot(x0,y_pchip,'b');
