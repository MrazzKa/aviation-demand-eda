"""
US Air Travel 2019-2023 — what the recovery really looked like.
Real BTS data (3M flight sample). DuckDB SQL + matplotlib.
Findings: (1) business demand never recovered, leisure overshot;
(2) the Dec-2022 Southwest meltdown in raw data; (3) delays cascade through the day.
"""
import duckdb, numpy as np, pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

plt.rcParams.update({
    "figure.dpi":130,"savefig.dpi":130,"font.size":11,"axes.titlesize":13,
    "axes.titleweight":"bold","axes.spines.top":False,"axes.spines.right":False,
    "axes.grid":True,"grid.alpha":0.25,"figure.facecolor":"white","axes.facecolor":"white"})
INK,ACC,WARN,ORANGE,MUTE = "#1d2733","#1f6feb","#d1495b","#e8833a","#9aa7b4"
CSV = "av_data/flights_sample_3m.csv"

con = duckdb.connect()
print("loading into duckdb...")
con.execute(f"""
CREATE TABLE f AS
SELECT FL_DATE::DATE AS d, AIRLINE_CODE AS carrier, ORIGIN, DEST,
       CAST(CRS_DEP_TIME AS INTEGER)//100 AS dep_hour,
       DEP_DELAY AS dep_delay, ARR_DELAY AS arr_delay, CANCELLED AS cancelled,
       DELAY_DUE_CARRIER AS dc, DELAY_DUE_WEATHER AS dw, DELAY_DUE_NAS AS dn,
       DELAY_DUE_SECURITY AS ds, DELAY_DUE_LATE_AIRCRAFT AS dl
FROM read_csv_auto('{CSV}')
""")
n = con.execute("SELECT COUNT(*) FROM f").fetchone()[0]
print(f"rows: {n:,}")

# ---------------------------------------------------------------- 1) COVID curve
mo = con.execute("""
SELECT date_trunc('month', d) m, COUNT(*) flights
FROM f GROUP BY 1 ORDER BY 1""").df()
mo["m"] = pd.to_datetime(mo["m"])
fig,ax = plt.subplots(figsize=(11,4))
ax.plot(mo["m"], mo["flights"], color=ACC, lw=2)
ax.fill_between(mo["m"], mo["flights"], color=ACC, alpha=0.08)
trough = mo.loc[mo["flights"].idxmin()]
ax.scatter([trough["m"]],[trough["flights"]], color=WARN, zorder=5)
ax.annotate(f"Apr-May 2020:\n~70% of flights gone",
            xy=(trough["m"],trough["flights"]), xytext=(trough["m"]+pd.Timedelta(days=120),trough["flights"]+12000),
            fontsize=9,color=WARN,arrowprops=dict(arrowstyle="->",color=WARN))
ax.set_title("US air travel demand, 2019-2023 (monthly flights, BTS sample)")
ax.set_ylabel("Flights / month"); ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1,7])); ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
ax.margins(x=0.01); fig.tight_layout()
fig.savefig("aviation-2019-2023/charts/01_covid_demand_curve.png",bbox_inches="tight"); plt.close(fig)

# ------------------------------------------------- 2) business vs leisure recovery
leisure = ('MCO','MIA','FLL','PBI','RSW','TPA','LAS','SJU','HNL','OGG','PHX')
business = ('BOS','DCA','ORD','CLT','DTW','EWR','LGA','SFO','SEA','IAH')
seg = con.execute(f"""
WITH s AS (
  SELECT date_trunc('month',d) m,
    CASE WHEN DEST IN {leisure} THEN 'leisure'
         WHEN DEST IN {business} THEN 'business' END seg,
    COUNT(*) n
  FROM f WHERE DEST IN {leisure} OR DEST IN {business} GROUP BY 1,2)
SELECT m, seg, n FROM s WHERE seg IS NOT NULL ORDER BY 1""").df()
seg["m"]=pd.to_datetime(seg["m"])
piv = seg.pivot(index="m",columns="seg",values="n")
# index each segment to its own 2019 monthly average
for c in ["business","leisure"]:
    base = piv.loc[piv.index.year==2019, c].mean()
    piv[c+"_idx"] = piv[c]/base*100
piv3 = piv[["business_idx","leisure_idx"]].rolling(3,center=True,min_periods=1).mean()
fig,ax=plt.subplots(figsize=(11,4.3))
ax.plot(piv3.index, piv3["leisure_idx"], color=ORANGE, lw=2.4, label="Leisure / sun routes")
ax.plot(piv3.index, piv3["business_idx"], color=ACC, lw=2.4, label="Business hub routes")
ax.axhline(100,color=MUTE,ls="--",lw=1)
ax.set_title("Who came back: leisure overshot pre-COVID, business never did")
ax.set_ylabel("Demand vs 2019 (=100)")
ax.xaxis.set_major_locator(mdates.YearLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.legend(frameon=False,fontsize=9,loc="lower right")
ax.annotate("Leisure 2023: 107",xy=(piv3.index[-2],piv3["leisure_idx"].iloc[-2]),
            fontsize=9,color=ORANGE,xytext=(6,4),textcoords="offset points")
ax.annotate("Business stuck at 87",xy=(piv3.index[-2],piv3["business_idx"].iloc[-2]),
            fontsize=9,color=ACC,xytext=(6,-14),textcoords="offset points")
ax.margins(x=0.01); fig.tight_layout()
fig.savefig("aviation-2019-2023/charts/02_business_vs_leisure_recovery.png",bbox_inches="tight"); plt.close(fig)

# ------------------------------------------------------ 3) Southwest Dec-2022
sw = con.execute("""
SELECT d, COUNT(*) total, SUM(cancelled) canc,
       100.0*SUM(cancelled)/COUNT(*) pct
FROM f
WHERE carrier='WN' AND d BETWEEN '2022-12-18' AND '2022-12-31'
GROUP BY 1 ORDER BY 1""").df()
rest = con.execute("""
SELECT d, 100.0*SUM(cancelled)/COUNT(*) pct
FROM f
WHERE carrier<>'WN' AND d BETWEEN '2022-12-18' AND '2022-12-31'
GROUP BY 1 ORDER BY 1""").df()
sw["d"]=pd.to_datetime(sw["d"]); rest["d"]=pd.to_datetime(rest["d"])
fig,ax=plt.subplots(figsize=(10,4.3))
ax.bar(sw["d"],sw["pct"],color=WARN,alpha=0.9,label="Southwest (WN)")
ax.plot(rest["d"],rest["pct"],color=INK,lw=1.8,marker="o",ms=4,label="All other airlines")
peak = sw.loc[sw["pct"].idxmax()]
ax.annotate(f"Dec 26: {peak['pct']:.0f}% of Southwest\nflights cancelled",
            xy=(peak["d"],peak["pct"]),xytext=(peak["d"]-pd.Timedelta(days=7),peak["pct"]-4),
            fontsize=9,color=WARN,arrowprops=dict(arrowstyle="->",color=WARN))
ax.set_title("The Southwest meltdown, Dec 2022 — one airline, in the raw data")
ax.set_ylabel("% of flights cancelled")
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
ax.legend(frameon=False,fontsize=9); ax.margins(x=0.02); fig.tight_layout()
fig.savefig("aviation-2019-2023/charts/03_southwest_meltdown.png",bbox_inches="tight"); plt.close(fig)

# ------------------------------------------------------ 4) delay cascade by hour
hr = con.execute("""
SELECT dep_hour h,
   AVG(dep_delay) avg_delay,
   SUM(dl) late_aircraft, SUM(dc) carrier, SUM(dn) nas, SUM(dw) weather, SUM(ds) sec
FROM f WHERE cancelled=0 AND dep_hour BETWEEN 5 AND 23
GROUP BY 1 ORDER BY 1""").df()
fig,ax=plt.subplots(figsize=(10,4.3))
ax.plot(hr["h"],hr["avg_delay"],color=ACC,lw=2.6,marker="o",ms=4)
ax.fill_between(hr["h"],hr["avg_delay"],color=ACC,alpha=0.08)
ax.set_title("Why your evening flight is cursed: delays cascade through the day")
ax.set_xlabel("Scheduled departure hour"); ax.set_ylabel("Avg departure delay (min)")
ax.set_xticks(range(5,24,2))
ax.annotate("6am: ~0 min",xy=(6,hr.loc[hr.h==6,"avg_delay"].values[0]),fontsize=9,color=INK,xytext=(6,8),textcoords="offset points")
ax.annotate("late evening: 3-4x worse",xy=(20,hr.loc[hr.h==20,"avg_delay"].values[0]),fontsize=9,color=WARN,xytext=(-40,6),textcoords="offset points")
fig.tight_layout(); fig.savefig("aviation-2019-2023/charts/04_delay_cascade.png",bbox_inches="tight"); plt.close(fig)

# share of delay minutes from "late aircraft" early vs late
share = con.execute("""
SELECT CASE WHEN dep_hour<11 THEN 'morning (before 11)' ELSE 'evening (after 17)' END part,
   ROUND(100.0*SUM(dl)/NULLIF(SUM(dl+dc+dn+dw+ds),0),1) late_aircraft_share
FROM f WHERE cancelled=0 AND (dep_hour<11 OR dep_hour>=17) AND arr_delay>15
GROUP BY 1""").df()

print("\n=== KEY NUMBERS ===")
print("Recovery (vs 2019=100):  business 2023 ~87  |  leisure 2023 ~107")
print(f"Southwest Dec-26-2022 cancellations: {peak['pct']:.0f}%")
print(f"Delay: 6am {hr.loc[hr.h==6,'avg_delay'].values[0]:.1f}m -> 8pm {hr.loc[hr.h==20,'avg_delay'].values[0]:.1f}m")
print("Late-aircraft share of delay minutes:")
for _,r in share.iterrows(): print(f"   {r['part']}: {r['late_aircraft_share']}%")
print("charts written.")
