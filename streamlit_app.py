#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import streamlit as st
import pandas as pd

from utils import normalize_kana
st.set_page_config(layout="wide")


class Database:
    def __init__(self):
        self.db = sqlite3.connect("data/pokemon-sv.db")
        self.db.create_function("normalize_kana", 1, normalize_kana)
    
    def get_query(self, query):
        print("Start query:", query)
        return pd.read_sql(query, self.db)
        print("End query")

db = Database()

@st.cache_data
def get_query(query):
    return db.get_query(query)

class const:
    monsters = get_query("""
    SELECT DISTINCT uname FROM monsters
    ORDER BY normalize_kana(uname)
    """).values[:,0]

    types = get_query("""
    SELECT * FROM (
        SELECT DISTINCT type1 AS type FROM monsters WHERE type1 IS NOT NULL 
        UNION
        SELECT DISTINCT type2 AS type FROM monsters WHERE type2 IS NOT NULL
    )
    ORDER BY type
    """).values[:,0]

    skills = get_query("""
    SELECT DISTINCT skill FROM skills
    ORDER BY normalize_kana(skill)
    """).values[:,0]

    specs = get_query("""
    SELECT DISTINCT spec FROM specs
    ORDER BY normalize_kana(spec)
    """).values[:,0]

    skill_attrs = [c for c in get_query("""
    SELECT * FROM skills
    """).columns if c[0] < "a" or c[0] >= "z"]

    skill_targets = get_query("""
    SELECT DISTINCT target FROM skills
    ORDER BY normalize_kana(target)
    """).values[:,0]

    power_max = get_query("""
    SELECT MAX(pw) FROM skills
    """).values[0,0]

    power_min = get_query("""
    SELECT MIN(pw) FROM skills
    """).values[0,0]

    hit_max = get_query("""
    SELECT MAX(hit) FROM skills
    """).values[0,0]

    hit_min = get_query("""
    SELECT MIN(hit) FROM skills
    """).values[0,0]

    skill_percents = get_query("""
    SELECT DISTINCT CASE WHEN percent IS NULL THEN 'NA' ELSE CAST(percent AS TEXT) END AS p FROM skills
    ORDER BY percent NULLS LAST
    """).values[:,0]


    table_width = 1000
    table_height = 700


# initialize state variables
for key in ["select_pokemon_name_value", "select_skill1_value", "select_skill2_value", "select_spec_value"]:
    if key not in st.session_state:
          st.session_state[key] = None

def main():
    st.markdown(
        """
        <style>
            section[data-testid="stSidebar"] {
                width: 400px !important; # Set the width to your desired value
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    tab_monster, tab_skill, tab_spec, tab_item = st.tabs(["ポケモン", "技", "特性", "持ち物"])

    with st.sidebar:
        select_pokemon_name = st.multiselect("ポケモン", const.monsters, default=st.session_state["select_pokemon_name_value"])
        st.session_state["select_pokemon_name_value"] = None
        col1, col2 = st.columns([1, 1])
        select_pokemon_type = col1.multiselect("タイプ1", const.types)
        select_pokemon_type2 = col2.multiselect("タイプ2", const.types)
        
        col1, col2 = st.columns([1, 1])
        # If session_state has the desired values to use, we use it as default
        # and we delete the value (we consumed it just once)
        # Otherwise, the button does not work when we delete the values and hit the button again,
        # since there is no value change
        select_skill = col1.multiselect("技1", const.skills, default=st.session_state["select_skill1_value"])
        select_skill2 = col2.multiselect("技2", const.skills, default=st.session_state["select_skill2_value"])
        st.session_state["select_skill1_value"] = None
        st.session_state["select_skill2_value"] = None
        col1, col2 = st.columns([6, 4])
        select_spec = col1.multiselect("特性", const.specs, default=st.session_state["select_spec_value"])
        st.session_state["select_spec_value"] = None
        select_evolve = col2.multiselect("進化形", ["最終形のみ", "最終形以外"])
        st.markdown("----")
        
        col1, col2 = st.columns([1, 1])
        select_skill_class = col1.multiselect("種別", ["物理", "特殊", "変化"])
        select_skill_contact = col2.multiselect("接触有無", ["接触", "非接触"])
        col1, col2 = st.columns([7, 5])
        select_skill_attr = col1.multiselect("技特徴", const.skill_attrs)
        select_skill_target = col2.multiselect("対象", const.skill_targets)
        #select_skill_percent = col2.multiselect("確率", const.skill_percents)
        col1, col2 = st.columns([1, 1])
        slider_skill_power = col1.slider("威力", min_value=const.power_min, max_value=const.power_max, 
                                         value=[const.power_min, const.power_max], step=5)
        slider_skill_hit = col2.slider("命中率", min_value=const.hit_min, max_value=const.hit_max,
                                       value=[const.hit_min, const.hit_max], step=5)
        text_skill = st.text_input("技自由検索")
        text_spec = st.text_input("特性自由検索")
        text_item = st.text_input("持ち物自由検索")

        st.markdown("----")
        st.markdown("Data Source: [GameWith](https://gamewith.jp/pokemon-sv), [Game8](https://game8.jp/pokemon-sv)")
        st.markdown("Bug Report, Feedback: [GitHub](https://github.com/kota7/pokemon-sv-db/issues)")

    with tab_monster:
        filters = []
        if select_pokemon_type and select_pokemon_type2:
            t1 = tuple(select_pokemon_type + ["foo"])
            t2 = tuple(select_pokemon_type2 + ["foo"])
            filters.append(f"(m.type1 IN {t1} AND m.type2 IN {t2}) OR (m.type1 IN {t2} AND m.type2 IN {t1})")
        elif select_pokemon_type or select_pokemon_type2:
            t = tuple(select_pokemon_type + select_pokemon_type2 + ["foo"])
            filters.append(f"m.type1 IN {t} OR m.type2 IN {t}")
        if select_evolve:
            vals = [1 if c == "最終形のみ" else 0 if c == "最終形以外" else 99 for c in select_evolve] + [99]
            filters.append(f"m.evolve_final IN {tuple(vals)}")
        if select_pokemon_name:
            filters.append(f"m.uname IN {tuple(select_pokemon_name + ['foo'])}")
        if select_skill:
            filters.append(f"mk.skill IN {tuple(select_skill + ['foo'])}")
        if select_skill2:
            filters.append(f"mk2.skill IN {tuple(select_skill2 + ['foo'])}")
        if select_spec:
            filters.append(f"mp.spec IN {tuple(select_spec + ['foo'])}")
        filter = " AND ".join(f"( {f} )" for f in filters) if filters else "1"

        df = get_query(f"""
        SELECT DISTINCT
           m.uname AS name
          ,m.type1, m.type2, m.H, m.A, m.B, m.C, m.D, m.S, m.H + m.A + m.B + m.C + m.D + m.S AS total
          ,m.weight
          ,m.gender
          ,m.evolve_final AS final
          {',mk.skill' if select_skill else ""}
          {',mk2.skill AS skill2' if select_skill2 else ""}
          {''',CASE WHEN mp.spec_type = '夢特性' THEN mp.spec || '(夢)' ELSE mp.spec END AS spec''' if select_spec else ""}
          ,m.url AS url
        FROM
          monsters AS m
          {'INNER JOIN monster_skills AS mk ON m.uname = mk.uname' if select_skill else ''}
          {'INNER JOIN monster_skills AS mk2 ON m.uname = mk2.uname' if select_skill2 else ''}
          {'INNER JOIN monster_specs AS mp ON m.uname = mp.uname' if select_spec else ''}          
        WHERE {filter}
        ORDER BY normalize_kana(m.uname)
        """)
        st.data_editor(df, hide_index=True, width=const.table_width, height=const.table_height,
                       column_config={"url": st.column_config.LinkColumn()})
        button_apply_pokemon_name = st.button("ポケモンフィルタへコピー")
        if button_apply_pokemon_name:
            st.session_state["select_pokemon_name_value"] = tuple(df.name.tolist())
            st.rerun()

    with tab_skill:
        filters = []
        if text_skill:
            filters.append(f"k.skill LIKE '%{text_skill}%' OR k.desc LIKE '%{text_skill}%'")
        if select_skill_class:
            filters.append(f"k.class IN {tuple(select_skill_class + ['foo'])}")
        if select_skill_target:
            filters.append(f"k.target IN {tuple(select_skill_target + ['foo'])}")
        if select_skill_contact:
            vals = [0 if c == "非接触" else 1 if c == "接触" else 99 for c in select_skill_contact] + [99]
            filters.append(f"k.contact IN {tuple(vals)}")
        if select_pokemon_name:
            filters.append(f"mk.uname IN {tuple(select_pokemon_name + ['foo'])}")
        if select_skill_attr:
            for attr in select_skill_attr:
                filters.append(f"k.{attr}")
        filters.append("k.pw BETWEEN {} AND {}".format(*slider_skill_power))
        filters.append("k.hit BETWEEN {} AND {}".format(*slider_skill_hit))
        filter_ = " AND ".join(f"( {f} )" for f in filters) if filters else "1"

        orders = []
        if select_skill or select_skill2:
            vals = tuple(select_skill + select_skill2 + ['foo'])
            orders.append(f"CASE WHEN k.skill IN {vals} THEN 0 ELSE 1 END")
        if select_pokemon_name:
            orders.append("normalize_kana(mk.uname), mk.skill_order")
        orders.append("normalize_kana(k.skill)")
        order_ = ",".join(orders)

        df = get_query(f"""
        SELECT DISTINCT
          {'mk.uname,' if select_pokemon_name else ''}
           k.skill
          ,k.type
          ,k.class
          ,k.target
          ,k.pw
          ,k.hit
          ,k.pp
          ,k.attr
          ,k.percent
          ,k.desc
          ,k.url
        FROM
          skills AS k
          {'INNER JOIN monster_skills AS mk ON k.skill = mk.skill' if select_pokemon_name else ''}
        WHERE {filter_}
        ORDER BY {order_}
        """)
        st.data_editor(df, hide_index=True, width=const.table_width, height=const.table_height,
                       column_config={"url": st.column_config.LinkColumn()})
        col1, col2, col3 = st.columns([2,2,7])
        button_apply_skill1 = col1.button("技フィルタ1へコピー")
        button_apply_skill2 = col2.button("技フィルタ2へコピー")
        if button_apply_skill1:
            st.session_state["select_skill1_value"] = tuple(df.skill.tolist())
            st.rerun()
        if button_apply_skill2:
            st.session_state["select_skill2_value"] = tuple(df.skill.tolist())
            st.rerun()

    with tab_spec:
        filters = []
        if text_spec:
            filters.append(f"p.spec LIKE '%{text_spec}%' OR p.desc LIKE '%{text_spec}%'")
        if select_spec:
            filters.append(f"p.spec IN {tuple(select_spec + ['foo'])}")
        if select_pokemon_name:
            filters.append(f"mp.uname IN {tuple(select_pokemon_name + ['foo'])}")
        filter = " AND ".join(f"( {f} )" for f in filters) if filters else "1"
        df = get_query(f"""
        SELECT
          {'mp.uname, mp.spec_type AS spec_type,' if select_pokemon_name else ''}
          p.*
        FROM
          specs AS p
          {'INNER JOIN monster_specs AS mp ON p.spec = mp.spec' if select_pokemon_name else ''}
          WHERE {filter}
        ORDER BY normalize_kana(p.spec)
        """)
        st.data_editor(df, hide_index=True, width=const.table_width, height=const.table_height)
        button_apply_spec = st.button("特性フィルタへコピー")
        if button_apply_spec:
            st.session_state["select_spec_value"] = tuple(df.spec.tolist())
            st.rerun()

    with tab_item:
        filters = []
        if text_item:
            filters.append(f"item LIKE '%{text_item}%' OR desc LIKE '%{text_item}%'")
        filter = " AND ".join(f"( {f} )" for f in filters) if filters else "1"
        df = get_query(f"""
        SELECT * FROM items
          WHERE {filter}
        ORDER BY normalize_kana(item)
        """)
        st.data_editor(df, hide_index=True, width=const.table_width, height=const.table_height)


if __name__ == "__main__":
    main()