x=1:20;
y=x+sin(x);
[a_1,s_1]=polyfit(x,y,1);
[a_2,s_2]=polyfit(x,y,2);
[a_3,s_3]=polyfit(x,y,3);
z_1=polyval(a_1,x);
z_2=polyval(a_2,x);
z_3=polyval(a_3,x);
plot(x,y,'+');
hold on
x0=1:0.01:20;
z0_1=polyval(a_1,x0);
z0_2=polyval(a_2,x0);
z0_3=polyval(a_3,x0);
plot(x0,z0_1,'r',x0,z0_2,'b',x0,z0_3,'g');
