import streamlit as st
import pandas as pd
import sqlite3 
import hashlib
import datetime

scale=[[10,90,4,15,40],[20,45,3,9,21]]

conn = sqlite3.connect('database.db')
c = conn.cursor()

def make_hashes(password):
	return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password,hashed_text):
	if make_hashes(password) == hashed_text:
		return hashed_text
	return False

def create_user():
	c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT,password TEXT)')

def add_user(username,password):
	c.execute('INSERT INTO userstable(username,password) VALUES (?,?)',(username,password))
	conn.commit()

def login_user(username,password):
	c.execute('SELECT * FROM userstable WHERE username =? AND password = ?',(username,password))
	data = c.fetchall()
	return data



def login():
	#st.title("ログイン機能テスト")
	#menu = ["ホーム","ログイン","サインアップ"]
	st.set_page_config(page_title="進行時間",layout="wide")
	menu = ["ログイン"]
	choice = st.sidebar.selectbox("メニュー", menu)
	
	if choice == "ホーム":
		st.subheader("ホーム画面です")
	elif choice == "ログイン":
		#st.subheader("ログイン画面です")
		username = st.sidebar.text_input("ユーザー名を入力してください")
		password = st.sidebar.text_input("パスワードを入力してください",type='password')
		if st.sidebar.checkbox("ログイン"):
			create_user()
			hashed_pswd = make_hashes(password)
			result = login_user(username,check_hashes(password,hashed_pswd))
			if result:
				st.success("{}さんでログインしました".format(username))
				st.session_state.data=result
				return True
			else:
				st.warning("ユーザー名かパスワードが間違っています")

	elif choice == "サインアップ":
		st.subheader("新しいアカウントを作成します")
		new_user = st.text_input("ユーザー名を入力してください")
		new_password = st.text_input("パスワードを入力してください",type='password')

		if st.button("サインアップ"):
			create_user()
			add_user(new_user,make_hashes(new_password))
			st.success("アカウントの作成に成功しました")
			st.info("ログイン画面からログインしてください")

if __name__ == '__main__':
	if login():
		st.title('テスト版0.1')
		st.caption('これはstreamlitのテスト用のアプリです')
		st.subheader('締切時刻の重複確認プログラム')
		selected_item = st.radio('スケール',['10min', '20min'],horizontal=True)
		sel_scale=0 if selected_item=='10min' else 1

		#締切時刻の90マスにマッピングする関数
		def frameexpand(df1,df2):
			for k in range(len(df1)):
				##ilocではエラー「IndexError: iloc cannot enlarge its target objec」
				df2.loc[k]= [df1.iloc[k,0], df1.iloc[k,1], df1.iloc[k,2]]+['-' for i in range(scale[sel_scale][1])]
				for j in range(12):
					time_str = df1.iloc[k,3+j]
					time_obj = datetime.datetime.strptime(time_str, "%H:%M")
					for i in range(scale[sel_scale][1]):
						if time_obj < list_90[i]:
							df2.iloc[k,3+i]=time_obj.time().strftime("%H:%M")
							break
			return df2

		

		#時間軸リストの作成
		count_time=datetime.datetime(year=1900,month=1,day=1,hour=8,minute=scale[sel_scale][0])
		list_90=[]
		for i in range(scale[sel_scale][1]):
			list_90.append(count_time)
			count_time += datetime.timedelta(minutes=scale[sel_scale][0])
		li=['開催場','グレード','開催区分']+[str(list_90[i].time().strftime("%H:%M")) for i in range(scale[sel_scale][1])]

		df2=pd.DataFrame(columns=li)
		#df=pd.DataFrame()

		#初回起動時かどうかの判定・初期化処理
		if "count" not in st.session_state:
			st.session_state.count = 0

		#サイドバーにウィジェット
		uploaded_file=st.sidebar.file_uploader('場外発売管理システムの締切時刻一覧表をアップロードしてください。ファイル形式はxlsxに変更してください',type='xlsx')

		if uploaded_file:
			print('読み込み成功')
			
			df=pd.read_excel(uploaded_file,sheet_name=None)
			dflist=list(df)

			option=st.selectbox('開催日の選択',dflist)
			st.session_state.dflist=dflist
			st.session_state.option=option
			
			kaisai_date=str(df[option].iloc[1,1])[2:]+'('+str(df[option].iloc[0,15])+')'
			kaisai_count=str(df[option].iloc[2,1])[2:]
			kaisai_info=f'{kaisai_date} : {kaisai_count}'
			st.write('---')
			st.text(kaisai_info)
			st.session_state.kaisai_info=kaisai_info

			df[option].drop(df[option].index[[0,1,2,3,4]],inplace=True)
			df[option].drop(df[option].columns[1],axis=1,inplace=True)
			df[option].columns=['開催場','グレード','開催区分','1R','2R','3R','4R','5R','6R','7R','8R','9R','10R','11R','12R']
			dropIndex=df[option][df[option]['グレード'] =="-"].index
			df[option].drop(dropIndex,inplace=True)
			df[option].reset_index(drop=True,inplace=True)
			df[option].set_index('開催場')

			df2=frameexpand(df[option],df2)
			
			list_ALL=list((df2.iloc[:,3:].values).flatten())
			while '-' in list_ALL:
				list_ALL.remove('-')
			#print(len(list_ALL)-len(set(list_ALL)))

			duplicates = list(set([x for x in list_ALL if list_ALL.count(x) > 1]))
			duplicates.sort()
			st.session_state.duplicates=duplicates
			print(f'重複時刻：{duplicates}')

			st.write(f'<style>table {{border-collapse: collapse;}} table, th, td {{border: 1px solid black; padding: 5px;}}</style>', unsafe_allow_html=True)
			st.dataframe(df2.style.applymap(lambda x: 'background-color: yellow' if x in duplicates else 'background-color: white'))
			
			if len(duplicates) > 0:
				st.write(f'<span style="color:red">重複箇所:{duplicates}</span>', unsafe_allow_html=True)
			else:
				st.write(f'<span style="color:black">重複箇所はありません。皆様、ご協力ありがとうございました！complete!</span>', unsafe_allow_html=True)
				st.balloons()
			st.session_state['df']=df2
			st.session_state.count+=1

			# Excel ファイルに書き込む
			df2.style.applymap(lambda x: 'background-color: yellow' if x in duplicates else 'background-color: white').to_excel('output.xlsx', index=False,sheet_name=option)

			# ファイルをダウンロードする
			with open('output.xlsx', 'rb') as f:
				bytes = f.read()
				st.download_button('Download Excel', data=bytes, file_name='output.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
			st.write('---')
			tab1,tab2,tab3=st.tabs(['モーニング','デイ','ナイター'])
			with tab1:
				st.subheader('モーニング締切時刻')
				dfM=df2[df2['開催区分']=='モーニング']
				dfM=dfM.drop(li[3:scale[sel_scale][2]],axis=1)
				st.write(f'<style>table {{border-collapse: collapse;}} table, th, td {{border: 1px solid black; padding: 5px;}}</style>', unsafe_allow_html=True)
				st.dataframe(dfM.style.applymap(lambda x: 'background-color: yellow' if x in duplicates else 'background-color: white'))
				# Excel ファイルに書き込む
				dfM.style.applymap(lambda x: 'background-color: yellow' if x in duplicates else 'background-color: white').to_excel('output.xlsx', index=False,sheet_name=option)
				# ファイルをダウンロードする
				with open('output.xlsx', 'rb') as f:
					bytes = f.read()
					st.download_button('Download Excel', data=bytes, file_name='output_morning.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
			
			with tab2:
				st.subheader('デイ締切時刻（薄暮含む）')
				dfD=df2[(df2['開催区分']=='昼間') | (df2['開催区分']=='薄暮')]
				dfD=dfD.drop(li[3:scale[sel_scale][3]],axis=1)
				st.write(f'<style>table {{border-collapse: collapse;}} table, th, td {{border: 1px solid black; padding: 5px;}}</style>', unsafe_allow_html=True)
				st.dataframe(dfD.style.applymap(lambda x: 'background-color: yellow' if x in duplicates else 'background-color: white'))
				# Excel ファイルに書き込む
				dfD.style.applymap(lambda x: 'background-color: yellow' if x in duplicates else 'background-color: white').to_excel('output.xlsx', index=False,sheet_name=option)
				# ファイルをダウンロードする
				with open('output.xlsx', 'rb') as f:
					bytes = f.read()
					st.download_button('Download Excel', data=bytes, file_name='output_day.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

			with tab3:
				st.subheader('ナイター締切時刻（ミッドナイト含む）')
				dfN=df2[(df2['開催区分']=='ナイター') | (df2['開催区分']=='ミッドナイト')]
				dfN=dfN.drop(li[3:scale[sel_scale][4]],axis=1)
				st.write(f'<style>table {{border-collapse: collapse;}} table, th, td {{border: 1px solid black; padding: 5px;}}</style>', unsafe_allow_html=True)
				st.dataframe(dfN.style.applymap(lambda x: 'background-color: yellow' if x in duplicates else 'background-color: white'))
				# Excel ファイルに書き込む
				dfN.style.applymap(lambda x: 'background-color: yellow' if x in duplicates else 'background-color: white').to_excel('output.xlsx', index=False,sheet_name=option)
				# ファイルをダウンロードする
				with open('output.xlsx', 'rb') as f:
					bytes = f.read()
					st.download_button('Download Excel', data=bytes, file_name='output_nighter.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
		
		else:
			print('読み込みしていません')
			if st.session_state.count:
				option=st.selectbox('開催日の選択',st.session_state.dflist)
				st.text(st.session_state.kaisai_info)
				st.write(f'<style>table {{border-collapse: collapse;}} table, th, td {{border: 1px solid black; padding: 5px;}}</style>', unsafe_allow_html=True)
				
				st.dataframe(st.session_state['df'].style.applymap(lambda x: 'background-color: yellow' if x in st.session_state.duplicates else 'background-color: white'))
				#st.text(f'重複箇所:{st.session_state.duplicates}')
				if len(st.session_state.duplicates) > 0:
					st.write(f'<span style="color:red">重複箇所:{st.session_state.duplicates}</span>', unsafe_allow_html=True)
				else:
					st.write(f'<span style="color:black">重複箇所はありません。complete!</span>', unsafe_allow_html=True)
				

			