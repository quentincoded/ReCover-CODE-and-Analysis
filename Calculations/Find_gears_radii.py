import math
from math import pi

# def d1(d2,ds,theta,seil):
#     r2=d2/2
#     rs=ds/2
#     r1=(r2*rs*4*math.pi)/(3*seil)
#     return 2*r1
# def d2(d1,ds,theta,seil):
#     r1=d1/2
#     rs=ds/2 
#     r2=(seil*3*float(r1))/(4*math.pi*rs)
#     return 2*r2
# def ds(d1,d2,theta,seil):
#     r1=d1/2
#     r2=d2/2
#     rs=(seil*3*float(r1))/(4*math.pi*r2)
#     return 2*rs

# print("This program will help you find the radii of the gears in a gear train.")

# seil=float(input("Enter how long you want to extend the finders each: (d)"))
# print("Seil:",seil)
# degrees= float(input("Enter the turning degrees of Potentiometer:"))
# print("Degrees of Potentiometer are:",degrees)
# theta= float(degrees)*2*math.pi/360
# print("Theta= Turning angle is:",theta, "radians")
# choice= input("What Durchmesser you want to find? Enter 1 for d1, 2 for d2, s for ds:")
# if choice=="1":
#     d2= float(input("Enter d2:"))
#     ds= float(input("Enter ds:"))
#     print(d1(d2,ds,theta,seil))
# elif choice=="2":
#     d1= float(input("Enter Durchmesser of gear 1:"))
#     ds= float(input("Enter ds:"))
#     print("d2 should be then: ", str(d2(d1,ds,theta, seil)))
#     print

# else: ## choice=="s"
#     d1= float(input("Enter d1:"))
#     d2= float(input("Enter d2:"))
#     print(rs(d1,d2,theta, seil))




def r1(r2,rs,theta,seil):
    r1=(seil*3*float(r2))/(4*math.pi*rs)
    r1=(r2*rs*4*math.pi)/(3*seil)
    return r1
def r2(r1,rs,theta,seil):
    r2=(seil*3*float(r1))/(4*math.pi*rs)
    d2=2*r2
    return r2
def rs(r1,r2,theta,seil):
    rs=(seil*3*float(r1))/(4*math.pi*r2)
    return rs

tolerance=1
R_Potentiometer=15/2



print("This program will help you find the radii of the gears in a gear train. Please enter the values in mm.")

seil=float(input("Enter how long you want to extend the finders each: (d)"))
print("Seil:",seil)
degrees= float(input("Enter the turning degrees of Potentiometer:"))
print("Degrees of Potentiometer are:",degrees)
theta= float(degrees)*2*math.pi/360
print("Theta= Turning angle is:",theta, "radians")
choice= input("What do you want to find? Enter 1 for r1, 2 for r2, s for rs:")

if choice=="1":
    r2= float(input("Enter r2:"))
    rs= float(input("Enter rs:"))
    print(r1(r2,rs,theta,seil))
elif choice=="2":
    r1= float(input("Enter r1:"))
    rs= float(input("Enter rs:"))
    print("Druchmesser 2 should be then: " ,2*r2(r1,rs,theta, seil))

else: ## choice=="s"
    r1= float(input("Enter r1:"))
    r2= float(input("Enter r2:"))
    print(rs(r1,r2,theta, seil))

input("Press Enter to exit...")