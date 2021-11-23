import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

def plot_drive_ctl_data(data):
    fig, host = plt.subplots(figsize=(10,10))

    ax_error = host.twinx()
    ax_actual = host.twinx()

    host.set_xlabel("time(s)")
    host.set_ylim(-1.0, 1.0)
    ax_actual.set_ylim(0, 3000)
    ax_error.set_ylim(-2000, 2000)

    host.set_ylabel("percent output", color="tab:red")
    ax_error.set_ylabel("error", color="tab:green")
    ax_actual.set_ylabel("position", color="tab:blue")


    host.tick_params(axis="y", labelcolor="tab:red")
    ax_error.tick_params(axis="y", labelcolor="tab:green")
    ax_actual.tick_params(axis="y", labelcolor="tab:blue")

    host.xaxis.set_major_formatter(mdates.DateFormatter("%S.%f"))
    plt.gcf().autofmt_xdate()
    
    if len(data["setpoints"]) == 1:
        data["setpoints"].append(data["setpoints"][0])
        data["sp_times"].append(data["timestamps"][-1])
       

    p1, = host.plot(data["timestamps"], data["left_percent_out"], label="l output", color="tab:pink")
    p2, = host.plot(data["timestamps"], data["right_percent_out"], label="r output", color="tab:red")
    p3, = ax_error.plot(data["timestamps"], data["errors"], label="error", color="tab:green")
    p4, = ax_actual.plot(data["timestamps"], data["actual"], label="actual", color="tab:blue")
    p5, = ax_actual.plot(data["sp_times"], data["setpoints"], label="setpoint", color="tab:purple")



    host.legend(handles=[p1, p2, p3, p4, p5], loc="best")
    ax_actual.spines["right"].set_position(("outward", 80))

    plt.show()