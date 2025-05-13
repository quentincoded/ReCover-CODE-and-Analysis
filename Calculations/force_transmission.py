d_s=20
d_1=12
d_2=29
etha=1

F_finger=input("Enter the force applied by the finger: ")
F_finger=float(F_finger)

r_s=0.5*d_s
r_1=0.5*d_1
r_2=0.5*d_2


M_s=F_finger*r_s
M_1=M_s
i_1_2=d_2/d_1
M_2=etha*M_1*i_1_2
M_2*=2 ##double for the torque on the second gear
# print("The calculation is: M_2=etha*M_1*i_1_2*2" , etha ,"*" , i_1_2, "*" , 2)
print("The torque on the second gear is: ", M_2, "Nmm")
# i_1_2=M_2/(etha*M_1)
print("m1", M_1)
input("Press Enter to exit...")
