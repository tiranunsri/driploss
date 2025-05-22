import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib

# ✅ ฟอนต์ภาษาไทย
matplotlib.rcParams['font.family'] = 'Tahoma'

# 📥 โหลดข้อมูลจาก Google Drive (Public CSV link หรือแบบ direct .xlsx ผ่าน gdown)
import gdown
gdown.download('https://docs.google.com/spreadsheets/d/1jRYXViC1nEIM8gMy0RHy5cufIHRfdnFR/edit?usp=sharing&ouid=110281668206260656081&rtpof=true&sd=true', quiet=False)

# 📄 โหลดข้อมูล
df = pd.read_excel("driploss-v2.xlsx")
df['driploss'] = df['driploss'].astype(str).str.replace('%', '', regex=False).astype(float) * 100

# 🎛️ UI เริ่มต้น
st.markdown("<h4 style='font-weight:600;'>📊 วิเคราะห์ Drip Loss เปรียบเทียบโรงงาน</h4>", unsafe_allow_html=True)
products = df['สินค้า'].unique()
selected_product = st.selectbox("เลือกสินค้า", products)

# ✅ สไลด์ควบคุมอุณหภูมิ
room_min, room_max = df['Room Temp (°C)'].min(), df['Room Temp (°C)'].max()
item_min, item_max = df['Item Temp (°C)'].min(), df['Item Temp (°C)'].max()

room_range = st.slider("ช่วง Room Temp (°C)", float(room_min), float(room_max),
                       (float(room_min), float(room_max)), step=0.1)
item_range = st.slider("ช่วง Item Temp (°C)", float(item_min), float(item_max),
                       (float(item_min), float(item_max)), step=0.1)

# 🔍 กรองข้อมูล
df_filtered = df[
    (df['สินค้า'] == selected_product) &
    (df['Room Temp (°C)'].between(*room_range)) &
    (df['Item Temp (°C)'].between(*item_range)) &
    (df['driploss'].notnull())
].copy()

all_factories = sorted(df_filtered['Factory'].unique())
selected_factories = st.multiselect("เลือกโรงงานที่ต้องการแสดง", all_factories, default=all_factories)

df_selected = df_filtered[df_filtered['Factory'].isin(selected_factories)].copy()
if df_selected.empty:
    st.warning("⚠️ ไม่พบข้อมูลภายใต้เงื่อนไขที่เลือก")
    st.stop()

# ➕ รวมโรงงาน
df_combined = df_selected.copy()
df_combined['Factory'] = 'รวมทุกโรงงาน'
df_all = pd.concat([df_selected, df_combined])

# 📦 Box Plot
ordered_factories = sorted(df_selected['Factory'].unique()) + ['รวมทุกโรงงาน']
df_all['Factory'] = pd.Categorical(df_all['Factory'], categories=ordered_factories, ordered=True)
df_all.sort_values('Factory', inplace=True)

st.subheader(f"📦 % Drip loss - {selected_product}")
fig, ax = plt.subplots(figsize=(14, 7))
df_all.boxplot(column='driploss', by='Factory', ax=ax, patch_artist=True, grid=False)

# 🎨 สี box
for i, patch in enumerate(ax.artists):
    factory_name = ordered_factories[i]
    color = '#fce570' if factory_name == 'รวมทุกโรงงาน' else '#e0e0e0'
    patch.set_facecolor(color)

# 🎯 แกนและเส้นประ
ax.set_yticks(np.round(ax.get_yticks(), 2))
ax.set_yticklabels([f"{y:.2f}" for y in ax.get_yticks()], fontsize=10)
ax.set_xlabel("โรงงาน", fontsize=0)
ax.set_ylabel("Drip Loss (%)", fontsize=13)

ax.axhline(0, color='red', linestyle='--', linewidth=1, label='0%')
ax.axhline(1, color='orange', linestyle='--', linewidth=1, label='1%')
ax.axhline(1.5, color='green', linestyle='--', linewidth=1, label='1.5%')
ax.legend(loc='upper right', fontsize=9)

ax.set_title("")
plt.suptitle("")
ax.set_ylim(bottom=0)

# ✅ ดึงตำแหน่ง tick จริง
tick_positions = ax.get_xticks()
tick_labels = [label.get_text() for label in ax.get_xticklabels()]
ax.set_xticklabels([""] * len(tick_positions))  # ซ่อน label เดิม

# ✅ วาง label โดยใช้ tick position ตรงกับ box
y_base = -1.0
spacing = 0.35
for x, label in zip(tick_positions, tick_labels):
    subset = df_all[df_all['Factory'] == label]
    if subset.empty:
        continue
    mean_dl = subset['driploss'].mean()
    mean_room = subset['Room Temp (°C)'].mean()
    mean_item = subset['Item Temp (°C)'].mean()

    ax.text(x, y_base, label, ha='center', fontsize=12, weight='bold', color='navy')
    ax.text(x, y_base - spacing, f"DL: {mean_dl:.2f}%", ha='center', fontsize=10)
    ax.text(x, y_base - 2 * spacing, f"RT: {mean_room:.2f}°C", ha='center', fontsize=9)
    ax.text(x, y_base - 3 * spacing, f"IT: {mean_item:.2f}°C", ha='center', fontsize=9)

# 📊 แสดงกราฟ
st.pyplot(fig)

# 📋 สรุปตาราง
st.subheader("📋 สถิติของ Drip Loss")
summary = df_all.groupby('Factory').agg(
    N=('driploss', lambda x: x.dropna().shape[0]),
    Mean_DripLoss=('driploss', 'mean'),
    Q1=('driploss', lambda x: x.quantile(0.25)),
    Q3=('driploss', lambda x: x.quantile(0.75)),
    Lower_Whisker=('driploss', lambda x: x.quantile(0.25) - 1.5 * (x.quantile(0.75) - x.quantile(0.25))),
    Upper_Whisker=('driploss', lambda x: x.quantile(0.75) + 1.5 * (x.quantile(0.75) - x.quantile(0.25)))
).round(2)

st.dataframe(summary.reset_index(), use_container_width=True)