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
        return pd.read_sql(query, self.db)

db = Database()

class const:
    types = db.get_query("""
    SELECT DISTINCT type1 AS type FROM monsters WHERE type1 IS NOT NULL 
    UNION
    SELECT DISTINCT type2 AS type FROM monsters WHERE type2 IS NOT NULL
    ORDER BY 1
    """).values[:,0]

    skills = db.get_query("""
    SELECT DISTINCT skill FROM skills ORDER BY 1
    """).values[:,0]

    specs = db.get_query("""
    SELECT DISTINCT spec FROM specs ORDER BY 1
    """).values[:,0]





def main():
    with st.sidebar:
        select_mode = st.selectbox("探すのは・・・", ("ポケモン", "技", "特性"), index=0)
        if select_mode == "ポケモン":
            select_pokemon_type = st.multiselect("タイプ", const.types)
            select_skill = st.multiselect("覚える技", const.skills)
            select_spec = st.multiselect("特性", const.specs)
            

        #select_word_pair_limit = st.selectbox("Word pair limit", (50000, 100000, 500000, 1000000), index=2)
        #select_candidate_sample = st.selectbox("Candidate sample size", (250, 500, 1000, 2000), index=1)
    if select_mode == "ポケモン":
        filters = []
        if select_pokemon_type:
            filters.append(f"a.type1 IN {tuple(select_pokemon_type + ['foo'])} OR a.type2 IN {tuple(select_pokemon_type + ['foo'])}")
        if select_skill:
            filters.append(f"b.skill IN {tuple(select_skill + ['foo'])}")
        if select_spec:
            filters.append(f"c.spec IN {tuple(select_spec  + ['foo'])}")
        filter = " AND ".join(f"( {f} )" for f in filters) if filters else "1"

        df = db.get_query(f"""
        SELECT DISTINCT
          a.uname, a.type1, a.type2, a.H, a.A, a.B, a.C, a.D, a.S, a.H + a.A + a.B + a.C + a.D + a.S AS total
          {',b.skill' if select_skill else ""}
          {',c.spec' if select_spec else ""}
        FROM
          monsters AS a
          INNER JOIN monster_skills AS b
            ON a.uname = b.uname
          INNER JOIN monster_specs AS c
            ON a.uname = c.uname
        WHERE {filter}
        ORDER BY a.uname
        """)
        st.data_editor(df, hide_index=True, width=800, height=800)
    elif select_mode == "技":
        df = db.get_query("""
        SELECT * FROM skills ORDER BY skill
        """)
        st.data_editor(df, hide_index=True, width=800, height=800)
    elif select_mode == "特性":
        df = db.get_query("""
        SELECT * FROM specs ORDER BY spec
        """)
        st.data_editor(df, hide_index=True, width=800, height=800)


if __name__ == "__main__":
    main()