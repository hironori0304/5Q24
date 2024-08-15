import streamlit as st
import pandas as pd
import random

# クイズデータを読み込む関数
def load_quizzes(file):
    df = pd.read_csv(file, encoding='utf-8')
    return df

# アプリケーションのタイトル
st.title('国家試験対策アプリ')

# セッション状態の初期化
if 'highlighted_questions' not in st.session_state:
    st.session_state.highlighted_questions = set()
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {}
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'total_questions' not in st.session_state:
    st.session_state.total_questions = 0
if 'name' not in st.session_state:
    st.session_state.name = ""
if 'percentage' not in st.session_state:
    st.session_state.percentage = 0

# ファイルアップロード
uploaded_file = st.file_uploader("クイズデータのCSVファイルをアップロードしてください", type="csv")

if uploaded_file is not None:
    # アップロードされたファイルを読み込む
    df = load_quizzes(uploaded_file)
    
    # 年と分類の選択肢を取得し、「すべて」を追加
    years = ['未選択'] + df['year'].unique().tolist() + ['すべて']
    categories = ['未選択'] + df['category'].unique().tolist() + ['すべて']
    
    # ユーザーが「年」と「分類」を選択
    selected_year = st.selectbox('年を選択してください', years)
    selected_category = st.selectbox('分類を選択してください', categories)
    
    # 年と分類の選択に応じてデータをフィルタリング
    if selected_year == '未選択' and selected_category == '未選択':
        filtered_df = pd.DataFrame()
    elif selected_year == 'すべて' and selected_category == 'すべて':
        filtered_df = df
    elif selected_year == 'すべて':
        filtered_df = df[df['category'] == selected_category]
    elif selected_category == 'すべて':
        filtered_df = df[df['year'] == selected_year]
    else:
        filtered_df = df[(df['year'] == selected_year) & (df['category'] == selected_category)]
    
    # 年と分類の選択が行われていない場合や、選択に合致する問題がない場合は問題を表示しない
    if filtered_df.empty:
        st.write("選択した条件に該当する問題がありません。")
    else:
        quizzes = []
        for _, row in filtered_df.iterrows():
            options = [row[f"option{i}"] for i in range(1, 6) if pd.notna(row[f"option{i}"])]
            answers = [row[f"answer{i}"] for i in range(1, 6) if pd.notna(row[f"answer{i}"])]

            # シャッフルされた選択肢をセッション状態に保存
            if 'shuffled_options' not in st.session_state:
                st.session_state.shuffled_options = {}
            if row["question"] not in st.session_state.shuffled_options:
                shuffled_options = options[:]
                random.shuffle(shuffled_options)
                st.session_state.shuffled_options[row["question"]] = shuffled_options

            quiz = {
                "question": row["question"],
                "type": row["type"],
                "options": st.session_state.shuffled_options[row["question"]],
                "answers": answers
            }
            quizzes.append(quiz)

        # ユーザーの回答を保存するための辞書
        user_answers = st.session_state.user_answers

        # クイズの表示とユーザー回答の収集
        for idx, quiz in enumerate(quizzes, start=1):
            # 問題番号のハイライト
            highlight = 'background-color: #fdd; padding: 10px;' if idx in st.session_state.highlighted_questions else ''
            st.markdown(f'<div style="{highlight}">問題{idx}</div>', unsafe_allow_html=True)

            # 問題文の表示
            st.markdown(f'<div>{quiz["question"]}</div>', unsafe_allow_html=True)

            # CSSで選択肢間隔を調整
            st.markdown(
                """
                <style>
                div[role='radiogroup'] {
                    margin-top: -20px;  /* 問題文と選択肢の間隔を完全に詰める */
                }
                div[role='radiogroup'] > label {
                    margin-bottom: 10px; /* 選択肢同士の間隔 */
                }
                </style>
                """,
                unsafe_allow_html=True
            )

            if quiz["type"] == "single":
                # 単一選択問題
                if quiz["question"] not in user_answers:
                    user_answers[quiz["question"]] = st.radio(
                        "",  # ラベルなし
                        quiz["options"],
                        key=f"{idx}_radio",
                        index=None  # 初期状態で何も選択されていない
                    )
                else:
                    answer = user_answers.get(quiz["question"])
                    # ユーザーが選択した回答がオプションリストに存在する場合にインデックスを取得
                    index = quiz["options"].index(answer) if answer in quiz["options"] else None
                    st.radio(
                        "",  # ラベルなし
                        quiz["options"],
                        key=f"{idx}_radio",
                        index=index
                    )
            elif quiz["type"] == "multiple":
                # 複数選択問題
                selected_options = user_answers.get(quiz["question"], [])
                if selected_options is None:
                    selected_options = []

                for option in quiz["options"]:
                    checked = option in selected_options
                    if st.checkbox(option, key=f"{idx}_{option}", value=checked):
                        if option not in selected_options:
                            selected_options.append(option)
                    else:
                        if option in selected_options:
                            selected_options.remove(option)
                user_answers[quiz["question"]] = selected_options

            # 問題間のスペース
            st.markdown("<br>", unsafe_allow_html=True)

        # 回答ボタンを作成
        if st.button('回答'):
            correct_count = 0
            total_questions = len(quizzes)
            for idx, quiz in enumerate(quizzes, start=1):
                if quiz["type"] == "single":
                    user_answer = user_answers.get(quiz["question"])
                    is_correct = user_answer == quiz["answers"][0]
                    if is_correct:
                        correct_count += 1
                        st.session_state.highlighted_questions.discard(idx)
                    else:
                        st.session_state.highlighted_questions.add(idx)
                elif quiz["type"] == "multiple":
                    user_answers_options = set(user_answers.get(quiz["question"], []))
                    correct_answers = set(quiz["answers"])
                    is_correct = user_answers_options == correct_answers
                    if is_correct:
                        correct_count += 1
                        st.session_state.highlighted_questions.discard(idx)
                    else:
                        st.session_state.highlighted_questions.add(idx)

            # 結果の表示
            st.write(f"正答数: {correct_count}/{total_questions}")
