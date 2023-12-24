#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import streamlit as st
import pandas as pd
st.set_page_config(layout="wide")

class Database:
    def __init__(self):
        self.db = sqlite3.connect("data/pokemon-sv.db")
    
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
    ORDER BY 1
    """).values[:,0]

    types = get_query("""
    SELECT DISTINCT type1 AS type FROM monsters WHERE type1 IS NOT NULL 
    UNION
    SELECT DISTINCT type2 AS type FROM monsters WHERE type2 IS NOT NULL
    ORDER BY 1
    """).values[:,0]

    skills = get_query("""
    SELECT DISTINCT skill FROM skills ORDER BY 1
    """).values[:,0]

    specs = get_query("""
    SELECT DISTINCT spec FROM specs ORDER BY 1
    """).values[:,0]

    table_width = 1000
    table_height = 700


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
    with st.sidebar:
        select_pokemon_name = st.multiselect("ポケモン", const.monsters)
        col1, col2 = st.columns([1, 1])
        select_pokemon_type = col1.multiselect("タイプ1", const.types)
        select_pokemon_type2 = col2.multiselect("タイプ2", const.types)
        
        col1, col2 = st.columns([1, 1])
        select_skill = col1.multiselect("技1", const.skills)
        select_skill2 = col2.multiselect("技2", const.skills)
        select_spec = st.multiselect("特性", const.specs)

        text_skill = st.text_input("技検索")
        text_spec = st.text_input("特性検索")
        text_item = st.text_input("持ち物検索")

        st.markdown("----")
        st.markdown("Data Source: [GameWith](https://gamewith.jp/pokemon-sv)")
        st.markdown("Bug Report, Feedback: [GitHub](https://github.com/kota7/pokemon-sv-db/issues)")

    tab_monster, tab_skill, tab_spec, tab_item = st.tabs(["ポケモン", "技", "特性", "持ち物"])
    with tab_monster:
        filters = []
        if select_pokemon_type and select_pokemon_type2:
            t1 = tuple(select_pokemon_type + ["foo"])
            t2 = tuple(select_pokemon_type2 + ["foo"])
            filters.append(f"(m.type1 IN {t1} AND m.type2 IN {t2}) OR (m.type1 IN {t2} AND m.type2 IN {t1})")
        elif select_pokemon_type or select_pokemon_type2:
            t = tuple(select_pokemon_type + select_pokemon_type2 + ["foo"])
            filters.append(f"m.type1 IN {t} OR m.type2 IN {t}")
 
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
        ORDER BY m.uname
        """)
        st.data_editor(df, hide_index=True, width=const.table_width, height=const.table_height,
                       column_config={"url": st.column_config.LinkColumn()})

    with tab_skill:
        filters = []
        if text_skill:
            filters.append(f"k.skill LIKE '%{text_skill}%' OR k.desc LIKE '%{text_skill}%'")
        if select_skill or select_skill2:
            filters.append(f"k.skill IN {tuple(select_skill + select_skill2 + ['foo'])} OR desc IN {tuple(select_skill + select_skill2 + ['foo'])}")
        if select_pokemon_name:
            filters.append(f"mk.uname IN {tuple(select_pokemon_name + ['foo'])}")
        filter = " AND ".join(f"( {f} )" for f in filters) if filters else "1"
        df = get_query(f"""
        SELECT DISTINCT
          {'mk.uname,' if select_pokemon_name else ''}
          k.*
        FROM
          skills AS k
          {'INNER JOIN monster_skills AS mk ON k.skill = mk.skill' if select_pokemon_name else ''}
        WHERE {filter}
        ORDER BY k.skill
        """)
        st.data_editor(df, hide_index=True, width=const.table_width, height=const.table_height)

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
        ORDER BY p.spec
        """)
        st.data_editor(df, hide_index=True, width=const.table_width, height=const.table_height)

    with tab_item:
        filters = []
        if text_item:
            filters.append(f"item LIKE '%{text_item}%' OR desc LIKE '%{text_item}%'")
        filter = " AND ".join(f"( {f} )" for f in filters) if filters else "1"
        df = get_query(f"""
        SELECT * FROM items
          WHERE {filter}
        ORDER BY item
        """)
        st.data_editor(df, hide_index=True, width=const.table_width, height=const.table_height)


if __name__ == "__main__":
    main()