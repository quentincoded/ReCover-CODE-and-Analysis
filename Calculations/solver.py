from sympy import symbols, Eq, solve
import math
import numpy as np
import matplotlib.pyplot as plt

print("This program will help you find the radii of the gears in a gear train.")

# Constants
tolerance = 2
R_Potentiometer = 15 / 2
distance = 100

# Define symbolic variables
r1, r2, rs = symbols('r1 r2 rs')

# Define equations


# Create an array of different values of rs
rs_values = np.linspace(2.5, 15, 50)  # Range of rs from 5 to 20, with 50 points

r1_values = []
r2_values = []

# Loop through each value of rs, solve the system, and store r1 and r2
for rs_val in rs_values:
    try:
        main_eq = Eq(r2, (distance * 3 * r1) / (4 * math.pi * rs))  
        fit_potentiometer = Eq(r1 + r2, R_Potentiometer + tolerance + rs + 1)
        dritt = Eq(rs, rs_val)
        solution = solve([main_eq, fit_potentiometer, dritt], (r1, r2, rs))
        
        # Ensure we have a real solution
        if solution and len(solution) > 0:
            # Extract real values, converting to float
            r1_val = float(solution[0][0])
            r2_val = float(solution[0][1])
            
            r1_values.append(r1_val)
            r2_values.append(r2_val)
    except Exception as e:
        print(f"Error solving for rs = {rs_val}: {e}")
        continue

# print(f"Found {len(r1_values)} solutions.")
# print(f"r1 = {r1_values}")
# print(f"r2 = {r2_values}")
# Convert lists to NumPy arrays
rs_values = np.array(rs_values[:len(r1_values)])
r1_values = np.array(r1_values)
r2_values = np.array(r2_values)

# Plot the results
plt.figure(figsize=(10, 6))
plt.plot(rs_values, r1_values, label='r1 (radius of gear 1)', marker='o')
plt.plot(rs_values, r2_values, label='r2 (radius of gear 2)', marker='s')
plt.xlabel('rs (radius of the spool for Seil)')
plt.ylabel('Radius Values')
plt.title('Radius vs rs for Gear Train')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()








tolerance = 2
R_Potentiometer = 15 / 2
r1, r2, rs = symbols('r1 r2 rs')
distance = 100

main_eq = Eq(r2,(distance * 3 * r1) / (4 * math.pi * rs))
fit_potentiometer=Eq(r1+r2 , R_Potentiometer+tolerance+rs+1)

# Create an array of different values of rs
rs_values = np.linspace(5, 20, 50)  # Range of rs from 5 to 20, with 50 points
r1_values = []
r2_values = []

dritt=Eq(rs,10)


solution = solve([main_eq, fit_potentiometer, dritt], (r1, r2, rs))
print(type(solution))
# for var, value in solution.items():
#     print(f"{var} = {value}"
print(len(solution))
print("r1=",solution[0][0])
print("r2=",solution[0] [1])
print("rs=",solution[0][2])

input("Press Enter to exit...")
