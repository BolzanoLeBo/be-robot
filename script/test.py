
T = 0.2
x1 = 0.2
x0 = 0
h = 0.05
z0= 0

#---------Parameters of x function-----------
a0 = x0
a1 = 0
a2 = -3 * (x0-x1)/T**2
a3 = 2 * (x0-x1)/T**3

#---------x calculus------------------------
#x = a3 * t**3 + a2 * t**2 + a1*t + a0
#---------Parameters of z function-----------
b0 = z0
b1 = 0 
b4 = (16*(h-z0))/T**4
b2 = (48*(z0-h))/T**2
b3 = (32*(z0-h))/T**3 

print(a0,a1,a2,a3)
#---------z calculus------------------------
#z = b4 * t**4 + b3 * t**3 + b2 * t**2 + b1 * t**1 + b0
#---------y calculus------------------------
#y = self.init[1] #we assume that y is constant 
