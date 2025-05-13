from tabulate import tabulate

# resistances=[500, 1000, 1800, 2000, 2200, 2400, 4000, 5000, 7000, 10000, 20000]
resistances=[i for i in range(500, 300000, 1000)]
r_var_min=49000 # 20k ohm
r_var_max=200000 # 100k ohm
v_bat=3.3

def calc_fsr_bottom(r_var, resistance, v_bat):
    v_out = (v_bat * r_var) / (r_var + resistance)
    return v_out
def calc_fsr_top(r_var, resistance, v_bat):
    v_out = (v_bat * resistance) / (r_var + resistance)
    return v_out

ranges_top = []
ranges_bottom = []
vmin_bottom = []
vmax_bottom = []
vmin_top = []
vmax_top = []
table = []



def round_to_3_decimal_places(value):
    return round(value, 3)

for i in resistances:
    # TOP configation
    v_out_top_min = calc_fsr_top(r_var_min, i, v_bat)
    v_out_top_max = calc_fsr_top(r_var_max, i, v_bat)
    voltage_range_top = abs(v_out_top_min - v_out_top_max)
    # append lists
    ranges_top.append(round_to_3_decimal_places(voltage_range_top))
    vmin_top.append(round_to_3_decimal_places(v_out_top_min))
    vmax_top.append(round_to_3_decimal_places(v_out_top_max))

    # bottom configuration
    v_out_bottom_min = calc_fsr_bottom(r_var_min, i, v_bat)
    v_out_bottom_max = calc_fsr_bottom(r_var_max, i, v_bat)
    voltage_range_bottom = abs(v_out_bottom_min - v_out_bottom_max)
    ranges_bottom.append(round_to_3_decimal_places(voltage_range_bottom))
    # append lists
    vmin_bottom.append(round_to_3_decimal_places(v_out_bottom_min))
    vmax_bottom.append(round_to_3_decimal_places(v_out_bottom_max))

   

   # Add both configs to the table
    table.append([i, 'Top', round(v_out_top_min, 3), round(v_out_top_max, 3), round(voltage_range_top, 3)])
    table.append([i, 'Bottom', round(v_out_bottom_min, 3), round(v_out_bottom_max, 3), round(voltage_range_bottom, 3)])

# this plots vmin vmax and range in respect to resiistance
import matplotlib.pyplot as plt

def plot_voltage_characteristics(resistances, vmin_top, vmax_top, ranges_top, vmin_bottom, vmax_bottom, ranges_bottom):
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=True)

    # Top configuration plot
    axes[0].plot(resistances, vmin_top, label='V_out Min', marker='o')
    axes[0].plot(resistances, vmax_top, label='V_out Max', marker='o')
    axes[0].plot(resistances, ranges_top, label='Voltage Range', marker='o')
    axes[0].set_title('Top Configuration')
    axes[0].set_xlabel('Resistance (Ω)')
    axes[0].set_ylabel('Voltage (V)')
    axes[0].legend()
    axes[0].grid(True)

    # Bottom configuration plot
    axes[1].plot(resistances, vmin_bottom, label='V_out Min', marker='o')
    axes[1].plot(resistances, vmax_bottom, label='V_out Max', marker='o')
    axes[1].plot(resistances, ranges_bottom, label='Voltage Range', marker='o')
    axes[1].set_title('Bottom Configuration')
    axes[1].set_xlabel('Resistance (Ω)')
    axes[1].legend()
    axes[1].grid(True)

    plt.tight_layout()
    plt.show()

# Call the function after your table is printed
plot_voltage_characteristics(resistances, vmin_top, vmax_top, ranges_top, vmin_bottom, vmax_bottom, ranges_bottom)



headers = ["Resistance (Ω)", "Configuration", "V_out Min (V)", "V_out Max (V)", "Voltage Range (V)"]
print(tabulate(table, headers=headers, tablefmt="grid"))