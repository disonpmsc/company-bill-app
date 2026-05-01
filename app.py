import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import plotly.express as px

# ---------------------- 全局样式 CSS ----------------------
st.markdown("""
<style>
div[data-testid="metric-container"] {background:transparent;padding:0;margin:0;}
div[data-testid="metric-container"] > div {font-size:14px !important;}
div[data-testid="metric-container"] label {font-size:12px !important;}
.st-table, .st-dataframe {font-size:13px;}
.bill-list-wrap {max-height: 600px; overflow-y: auto; padding-right:5px;}
</style>
""", unsafe_allow_html=True)

# ---------------------- 文件路径配置 ----------------------
COMPANY_FILE = "company_records.json"
COMPANY_CAT_FILE = "company_cats.json"

# ---------------------- 初始化数据 ----------------------
def init_all_data():
    if not os.path.exists(COMPANY_FILE):
        with open(COMPANY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)

    default_company = {
        "income": ["维修收入", "灌溉工程", "材料销售", "杂项营收"],
        "expense": ["加油燃油","材料费用","餐费","电话费用","工具费用","商业保险","汽车保险","汽车维保","学习费用","设备租赁费用"]
    }

    if os.path.exists(COMPANY_CAT_FILE):
        with open(COMPANY_CAT_FILE, "r", encoding="utf-8") as f:
            st.session_state.company_cats = json.load(f)
    else:
        st.session_state.company_cats = default_company
        with open(COMPANY_CAT_FILE, "w", encoding="utf-8") as f:
            json.dump(default_company, f, ensure_ascii=False, indent=2)

    if "company_records" not in st.session_state:
        with open(COMPANY_FILE, "r", encoding="utf-8") as f:
            st.session_state.company_records = json.load(f)

    if "edit_idx" not in st.session_state:
        st.session_state.edit_idx = None

# ---------------------- 保存函数 ----------------------
def save_records_data():
    with open(COMPANY_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.company_records, f, ensure_ascii=False, indent=2)

def save_cat_data():
    with open(COMPANY_CAT_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.company_cats, f, ensure_ascii=False, indent=2)

# ---------------------- 页面初始化 ----------------------
st.set_page_config(page_title="公司专用记账系统", layout="wide")
init_all_data()
st.title("🏢 公司专用记账系统")
cat_in = st.session_state.company_cats["income"]
cat_ex = st.session_state.company_cats["expense"]

# ---------------------- 分类管理模块 ----------------------
with st.expander("⚙️ 分类管理", expanded=False):
    t1, t2 = st.tabs(["收入类别", "支出类别"])
    with t1:
        new_in = st.text_input("新增收入")
        if st.button("➕ 添加收入", key="btn_add_in") and new_in.strip():
            if new_in not in cat_in:
                cat_in.append(new_in)
                save_cat_data()
                st.rerun()
        del_in = st.selectbox("删除收入项目", cat_in)
        if st.button("🗑️ 删除", key="btn_del_in"):
            cat_in.remove(del_in)
            save_cat_data()
            st.rerun()
    with t2:
        new_ex = st.text_input("新增支出")
        if st.button("➕ 添加支出", key="btn_add_ex") and new_ex.strip():
            if new_ex not in cat_ex:
                cat_ex.append(new_ex)
                save_cat_data()
                st.rerun()
        del_ex = st.selectbox("删除支出项目", cat_ex)
        if st.button("🗑️ 删除", key="btn_del_ex"):
            cat_ex.remove(del_ex)
            save_cat_data()
            st.rerun()

st.divider()

# ---------------------- 修改账单弹窗（修复版） ----------------------
if st.session_state.edit_idx is not None:
    idx = st.session_state.edit_idx
    data = st.session_state.company_records[idx]
    st.markdown("### ✏️ 修改账单")

    c1,c2 = st.columns(2)
    with c1:
        ed_date = st.date_input("日期", value=datetime.strptime(data["日期"], "%Y-%m-%d"), key="edit_date")
        ed_type = st.selectbox("类型", ["收入","支出"], 0 if data["类型"]=="收入" else 1, key="edit_type")
    with c2:
        cats = cat_in if ed_type=="收入" else cat_ex
        ed_cat = st.selectbox("类别", cats, cats.index(data["类别"]) if data["类别"] in cats else 0, key="edit_cat")

    old_net = float(data["净额(CAD)"])
    ed_net = st.number_input("税前金额(CAD)", value=old_net, min_value=0.0, step=0.01, key="edit_net")

    hst_mode = st.radio("HST", ["自动13%","手动输入"], horizontal=True, key="edit_hst_mode")

    if hst_mode == "自动13%":
        hst = round(ed_net * 0.13, 2)
    else:
        hst = st.number_input("HST金额", value=float(data["HST(CAD)"]), step=0.01, key="edit_hst_val")

    total = round(ed_net + hst, 2)
    st.info(f"✅ 税前: {ed_net:.2f} | HST: {hst:.2f} | 含税合计: {total:.2f}")
    note = st.text_input("备注", value=data["备注"], key="edit_note")

    b1,b2 = st.columns(2)
    with b1:
        if st.button("✅ 保存修改", use_container_width=True, key="edit_save"):
            st.session_state.company_records[idx] = {
                "日期":str(ed_date),
                "类型":ed_type,
                "类别":ed_cat,
                "净额(CAD)":ed_net,
                "HST(CAD)":hst,
                "总金额(CAD)":total,
                "备注":note
            }
            save_records_data()
            st.session_state.edit_idx = None
            st.rerun()
    with b2:
        if st.button("❌ 取消", use_container_width=True, key="edit_cancel"):
            st.session_state.edit_idx = None
            st.rerun()
    st.divider()

else:
    # ---------------------- 新增账单模块 ----------------------
    st.markdown("### 📝 新增账单")
    c1,c2 = st.columns(2)
    with c1:
        now_date = st.date_input("日期", datetime.today(), key="add_date")
        now_type = st.selectbox("类型", ["收入","支出"], key="add_type")
    with c2:
        now_cat = st.selectbox("类别", cat_in if now_type=="收入" else cat_ex, key="add_cat")

    hst_mode = st.radio("HST", ["自动13%","手动输入"], horizontal=True, key="add_hst_mode")
    net = st.number_input("税前金额(CAD)", min_value=0.0, step=0.01, key="add_net")

    if hst_mode == "自动13%":
        hst = round(net * 0.13, 2)
    else:
        hst = st.number_input("手动输入HST金额", min_value=0.0, step=0.01, key="add_hst")

    total = round(net + hst, 2)
    st.info(f"✅ 税前: {net:.2f} | HST: {hst:.2f} | 含税合计: {total:.2f}")
    note = st.text_input("备注", key="add_note")

    if st.button("➕ 新增保存", use_container_width=True, key="add_save_btn"):
        st.session_state.company_records.append({
            "日期":str(now_date),
            "类型":now_type,
            "类别":now_cat,
            "净额(CAD)":net,
            "HST(CAD)":hst,
            "总金额(CAD)":total,
            "备注":note
        })
        save_records_data()
        st.rerun()

# ---------------------- 账单列表 + 时间快捷键筛选 ----------------------
recs = st.session_state.company_records
if recs:
    st.divider()
    st.markdown("### 📋 账单明细（默认仅显示最近15天）")

    df = pd.DataFrame(recs)
    df["日期"] = pd.to_datetime(df["日期"])
    df = df.sort_values("日期", ascending=False)

    quick_date = st.radio(
        "快速选择时间段",
        ["最近15天", "最近30天", "本月", "上月", "全年", "自定义"],
        horizontal=True
    )

    today = datetime.now()
    if quick_date == "最近15天":
        s_d = (today - timedelta(days=15)).date()
        e_d = today.date()
    elif quick_date == "最近30天":
        s_d = (today - timedelta(days=30)).date()
        e_d = today.date()
    elif quick_date == "本月":
        s_d = today.replace(day=1).date()
        e_d = today.date()
    elif quick_date == "上月":
        if today.month == 1:
            last_month = 12
            last_year = today.year - 1
        else:
            last_month = today.month - 1
            last_year = today.year
        first_day_last = datetime(last_year, last_month, 1)
        if last_month == 12:
            next_month = 1
            next_year = last_year + 1
        else:
            next_month = last_month + 1
            next_year = last_year
        last_day_last = datetime(next_year, next_month, 1) - timedelta(days=1)
        s_d = first_day_last.date()
        e_d = last_day_last.date()
    elif quick_date == "全年":
        s_d = datetime(today.year, 1, 1).date()
        e_d = today.date()
    else:
        with st.expander("自定义时间段", expanded=True):
            c1,c2,c3 = st.columns(3)
            with c1:
                s_d = st.date_input("开始日期", (today - timedelta(days=15)).date(), key="filter_sd")
            with c2:
                e_d = st.date_input("结束日期", today.date(), key="filter_ed")
            with c3:
                tp = st.selectbox("收支类型", ["全部","收入","支出"], key="filter_tp")
                ct = st.selectbox("类别", ["全部"]+sorted(df["类别"].unique()), key="filter_ct")

    cond = (df["日期"] >= pd.to_datetime(s_d)) & (df["日期"] <= pd.to_datetime(e_d))
    if quick_date != "自定义":
        tp = st.selectbox("收支类型", ["全部","收入","支出"], key="filter_tp")
        ct = st.selectbox("类别", ["全部"]+sorted(df["类别"].unique()), key="filter_ct")
    if tp != "全部":
        cond &= df["类型"] == tp
    if ct != "全部":
        cond &= df["类别"] == ct
    df_show = df[cond]

    # 表头
    head = st.columns([1,0.7,1.2,0.8,0.8,1,1.2,0.6,0.6])
    head[0].write("**日期**")
    head[1].write("**类型**")
    head[2].write("**类别**")
    head[3].write("**税前**")
    head[4].write("**HST**")
    head[5].write("**合计**")
    head[6].write("**备注**")
    head[7].write("**修改**")
    head[8].write("**删除**")

    # 滚动账单列表
    st.markdown('<div class="bill-list-wrap">', unsafe_allow_html=True)
    for _, row_data in df_show.iterrows():
        ori_idx = int(row_data.name)
        c = st.columns([1,0.7,1.2,0.8,0.8,1,1.2,0.6,0.6])
        c[0].write(row_data["日期"].strftime("%Y-%m-%d"))
        c[1].write(row_data["类型"])
        c[2].write(row_data["类别"])
        c[3].write(f"{row_data['净额(CAD)']:.2f}")
        c[4].write(f"{row_data['HST(CAD)']:.2f}")
        c[5].write(f"{row_data['总金额(CAD)']:.2f}")
        c[6].write(row_data["备注"])

        with c[7]:
            if st.button("✏️", key=f"edit_btn_{ori_idx}"):
                st.session_state.edit_idx = ori_idx
                st.rerun()
        with c[8]:
            if st.button("🗑️", key=f"del_btn_{ori_idx}"):
                del st.session_state.company_records[ori_idx]
                save_records_data()
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # ---------------------- 支出统计图表 饼图+柱状图并排 ----------------------
    st.markdown("---")
    st.markdown("## 📊 细分类别统计")
    all_expense_cats = st.session_state.company_cats["expense"]
    df_all = pd.DataFrame(recs)
    df_all["日期"] = pd.to_datetime(df_all["日期"])
    df_ex = df_all[df_all["类型"]=="支出"].copy()

    if not df_ex.empty:
        cat_sum = df_ex.groupby("类别")["总金额(CAD)"].sum().reset_index()
        fixed_color_map = {
            "加油燃油": "#1f77b4",
            "材料费用": "#ff7f0e",
            "餐费": "#2ca02c",
            "电话费用": "#d62728",
            "工具费用": "#9467bd",
            "商业保险": "#8c564b",
            "汽车保险": "#e377c2",
            "汽车维保": "#7f7f7f",
            "学习费用": "#bcbd22",
            "设备租赁费用": "#17becf"
        }

        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            fig_cat_pie = px.pie(
                cat_sum, names="类别", values="总金额(CAD)",
                title="📌 支出类别占比", color="类别",
                color_discrete_map=fixed_color_map, height=350
            )
            st.plotly_chart(fig_cat_pie, use_container_width=True)
        with chart_col2:
            fig_cat_bar = px.bar(
                cat_sum, x="类别", y="总金额(CAD)",
                title="📌 各类别支出金额", color="类别",
                color_discrete_map=fixed_color_map, height=350
            )
            st.plotly_chart(fig_cat_bar, use_container_width=True)

    # ---------------------- 全类目汇总表 + 合计高亮 + 可下载 ----------------------
    st.markdown("---")
    st.markdown("## 🧾 全类目汇总｜税费总计")
    df_all["年月"] = df_all["日期"].dt.strftime("%Y-%m")

    cat_summary = []
    for cat in all_expense_cats:
        cat_df = df_ex[df_ex["类别"] == cat]
        pre = cat_df["净额(CAD)"].sum()
        hst = cat_df["HST(CAD)"].sum()
        total = cat_df["总金额(CAD)"].sum()
        cat_summary.append({
            "类别": cat,
            "净额(CAD)": round(pre, 2),
            "HST(CAD)": round(hst, 2),
            "总金额(CAD)": round(total, 2)
        })
    cat_summary_df = pd.DataFrame(cat_summary)

    # 合计行
    total_row = {
        "类别": "合计",
        "净额(CAD)": round(cat_summary_df["净额(CAD)"].sum(), 2),
        "HST(CAD)": round(cat_summary_df["HST(CAD)"].sum(), 2),
        "总金额(CAD)": round(cat_summary_df["总金额(CAD)"].sum(), 2)
    }
    cat_summary_df = pd.concat([cat_summary_df, pd.DataFrame([total_row])], ignore_index=True)

    # 合计行样式高亮
    def highlight_total(row):
        return ["background-color: #f0f2f6; font-weight: bold;" if row["类别"]=="合计" else "" for _ in row]

    styled_df = cat_summary_df.style.apply(highlight_total, axis=1)

    st.dataframe(
        styled_df,
        use_container_width=True,
        height=300,
        column_config={
            "类别": st.column_config.TextColumn("类别", width="medium"),
            "净额(CAD)": st.column_config.NumberColumn("净额(CAD)", width="small", format="%.2f"),
            "HST(CAD)": st.column_config.NumberColumn("HST(CAD)", width="small", format="%.2f"),
            "总金额(CAD)": st.column_config.NumberColumn("总金额(CAD)", width="small", format="%.2f")
        }
    )

    # 汇总表下载
    summary_csv = cat_summary_df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        "📥 下载全类目汇总表（发给财务用）",
        data=summary_csv,
        file_name="公司全类目支出汇总.csv",
        key="download_summary_csv_btn"
    )

    # ---------------------- 非标准13%税费：类别统计总览 + 明细清单 ----------------------
    st.markdown("---")
    st.markdown("## 📝 非标准13%税费单据（手动改税/免税）")

    # 1. 先逐笔筛选差异单据
    diff_list = []
    for _, row in df_all.iterrows():
        net_amt = float(row["净额(CAD)"])
        real_hst = float(row["HST(CAD)"])
        std_hst = round(net_amt * 0.13, 2)
        diff = round(real_hst - std_hst, 2)
        if abs(diff) > 0.01:
            diff_list.append({
                "日期": row["日期"].strftime("%Y-%m-%d"),
                "类型": row["类型"],
                "类别": row["类别"],
                "税前金额(CAD)": net_amt,
                "标准13%HST(CAD)": std_hst,
                "实际HST(CAD)": real_hst,
                "税费差额(CAD)": diff,
                "备注": row["备注"]
            })

    if diff_list:
        diff_df = pd.DataFrame(diff_list)

        # 2. 非标准税费 各类别统计总览
        st.markdown("### 📊 非标准税费｜各类别统计总览")
        cat_diff_stats = diff_df.groupby("类别").agg(
            单据笔数=("日期","count"),
            税前合计=("税前金额(CAD)","sum"),
            标准HST合计=("标准13%HST(CAD)","sum"),
            实际HST合计=("实际HST(CAD)","sum"),
            税费差额合计=("税费差额(CAD)","sum")
        ).reset_index()

        # 保留两位小数
        for col in ["税前合计","标准HST合计","实际HST合计","税费差额合计"]:
            cat_diff_stats[col] = round(cat_diff_stats[col],2)

        st.dataframe(cat_diff_stats, use_container_width=True, height=220)

        # 类别统计表下载
        stat_csv = cat_diff_stats.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            "📥 下载非标准税费类别统计表",
            data=stat_csv,
            file_name="非标准税费_类别统计总览.csv",
            key="download_stat_csv_btn"
        )

        # 3. 非标准明细清单
        st.markdown("### 📋 非标准税费逐笔明细清单")
        st.dataframe(diff_df, use_container_width=True, height=250)

        # 明细清单下载
        diff_csv = diff_df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            "📥 下载非标准税费明细清单",
            data=diff_csv,
            file_name="非13%税费手动单据明细.csv",
            key="download_diff_csv_btn"
        )

    else:
        st.success("✅ 所有单据均为标准13% HST，无手动改税/免税项目")

    # ---------------------- 公司财务总览 ----------------------
    st.divider()
    st.markdown("## 📊 公司财务总览")
    in_data = [x for x in recs if x["类型"]=="收入"]
    ex_data = [x for x in recs if x["类型"]=="支出"]

    sum_in_pre = sum(x["净额(CAD)"] for x in in_data)
    sum_ex_pre = sum(x["净额(CAD)"] for x in ex_data)
    sum_in_hst = sum(x["HST(CAD)"] for x in in_data)
    sum_ex_hst = sum(x["HST(CAD)"] for x in ex_data)
    sum_in_all = sum(x["总金额(CAD)"] for x in in_data)
    sum_ex_all = sum(x["总金额(CAD)"] for x in ex_data)

    c1,c2,c3,c4 = st.columns(4)
    with c1:
        st.write(f"收入税前: **${sum_in_pre:.2f}**")
        st.write(f"支出税前: **${sum_ex_pre:.2f}**")
    with c2:
        st.write(f"代收HST: **${sum_in_hst:.2f}**")
        st.write(f"付出HST: **${sum_ex_hst:.2f}**")
    with c3:
        st.write(f"含税总收入: **${sum_in_all:.2f}**")
        st.write(f"含税总支出: **${sum_ex_all:.2f}**")
    with c4:
        st.write(f"税前纯利: **${sum_in_pre - sum_ex_pre:.2f}**")
        st.write(f"含税结余: **${sum_in_all - sum_ex_all:.2f}**")

    # ---------------------- 报税专用CSV ----------------------
    st.markdown("---")
    st.markdown("## 📥 报税专用完整CSV")
    tax_df = df_all.copy()
    tax_df["年份"] = tax_df["日期"].dt.year
    tax_df["月份"] = tax_df["日期"].dt.month
    tax_csv = tax_df[["日期","年月","年份","月份","类型","类别","净额(CAD)","HST(CAD)","总金额(CAD)","备注"]]\
              .to_csv(index=False,encoding="utf-8-sig")
    st.download_button(
        "📁 下载完整分类报税CSV",
        data=tax_csv,
        file_name="Company_完整报税明细.csv",
        key="download_csv_btn"
    )

    # ====================== 年度收支统计表（无bug版） ======================
    st.markdown("---")
    st.markdown("## 📅 年度收支统计表（选择月份+类别查看明细）")

    # 选择年份
    year_sel = st.selectbox("选择统计年份", sorted(df_all["日期"].dt.year.unique(), reverse=True))
    df_year = df_all[df_all["日期"].dt.year == year_sel].copy()
    df_year["月份"] = df_year["日期"].dt.month

    # 固定支出类别作为行
    row_cats = st.session_state.company_cats["expense"]
    months = list(range(1,13))

    # 初始化月度矩阵
    month_total = {m:{cat:0.0 for cat in row_cats} for m in months}

    # 按月份、类别汇总金额
    for _, row in df_year.iterrows():
        if row["类型"] != "支出":
            continue
        m = row["日期"].month
        cat = row["类别"]
        if cat in row_cats:
            month_total[m][cat] += float(row["总金额(CAD)"])

    # 构造年度表数据
    table_data = []
    for cat in row_cats:
        row_dict = {"项目类别": cat}
        for m in months:
            row_dict[f"{m}月"] = round(month_total[m][cat],2)
        row_dict["年度合计"] = round(sum(month_total[m][cat] for m in months),2)
        table_data.append(row_dict)

    # 每月总支出合计行
    total_row = {"项目类别": "每月总支出"}
    yearly_sum = 0.0
    for m in months:
        m_sum = round(sum(month_total[m][cat] for cat in row_cats),2)
        total_row[f"{m}月"] = m_sum
        yearly_sum += m_sum
    total_row["年度合计"] = round(yearly_sum,2)
    table_data.append(total_row)

    # 转为DataFrame
    year_df = pd.DataFrame(table_data)

    # 样式：0标黄、合计行加深底色
    def style_year_table(df):
        sty = pd.DataFrame("", index=df.index, columns=df.columns)
        for r in df.index:
            for c in df.columns:
                if c not in ["项目类别"] and df.loc[r,c] == 0:
                    sty.loc[r,c] = "background-color:#FFFF99"
        sty.iloc[-1,:] = "background-color:#e6f7ff; font-weight:bold;"
        return sty

    styled_year_df = year_df.style.apply(style_year_table, axis=None).format(precision=2)
    st.dataframe(styled_year_df, use_container_width=True, height=600)

    # 用选择框查看明细
    col1, col2 = st.columns(2)
    with col1:
        sel_month = st.selectbox("选择月份", [f"{m}月" for m in months])
    with col2:
        sel_cat = st.selectbox("选择类别", year_df["项目类别"].tolist())

    sel_month_num = int(sel_month.replace("月",""))
    st.markdown(f"---\n### 📝 【{year_sel}年{sel_month} - {sel_cat}】账单明细")

    if sel_cat == "每月总支出":
        detail_df = df_year[(df_year["类型"]=="支出") & (df_year["月份"]==sel_month_num)].copy()
    else:
        detail_df = df_year[(df_year["类型"]=="支出") & (df_year["类别"]==sel_cat) & (df_year["月份"]==sel_month_num)].copy()

    if not detail_df.empty:
        detail_df = detail_df.sort_values("日期")
        show_cols = detail_df[["日期","类别","净额(CAD)","HST(CAD)","总金额(CAD)","备注"]]
        st.dataframe(show_cols, use_container_width=True)

        # 自动算合计，和表格数字对比
        month_sum = detail_df["总金额(CAD)"].sum()
        table_sum = year_df.loc[year_df["项目类别"]==sel_cat, sel_month].values[0]
        st.info(f"✅ 明细合计：${month_sum:.2f} | 表格显示：${table_sum:.2f} | 差额：${abs(month_sum - table_sum):.2f}")

        # 导出当前明细CSV
        detail_csv = detail_df[["日期","类别","净额(CAD)","HST(CAD)","总金额(CAD)","备注"]].to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            "📥 导出当前明细CSV",
            data=detail_csv,
            file_name=f"{year_sel}年{sel_month}_{sel_cat}_明细.csv"
        )
    else:
        st.info("该月份无此类别支出记录")

    # 下载整张年度收支统计表
    year_csv = year_df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        "📥 下载本年度收支统计表",
        data=year_csv,
        file_name=f"{year_sel}_公司年度收支统计表含月度总支出.csv"
    )
    # =====================================================================

else:
    st.info("暂无账单记录，请添加第一条公司收支。")