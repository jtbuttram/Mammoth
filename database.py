import sqlite3

conn = sqlite3.connect('mammoth.db')
c = conn.cursor()

def addTable(tableName):
	'''
	SQLite natively supports the following types: NULL, INTEGER, REAL, TEXT, BLOB.

	The following Python types can thus be sent to SQLite without any problem:

	Python type			SQLite type
	None				NULL
	int					INTEGER
	long				INTEGER
	float				REAL
	str (UTF8-encoded)	TEXT
	unicode				TEXT
	buffer				BLOB
	
	This is how SQLite types are converted to Python types by default:

	SQLite type			Python type
	NULL				None
	INTEGER				int or long, depending on size
	REAL				float
	TEXT				depends on text_factory, unicode by default
	BLOB				buffer
	'''
	# Create table
	#c.execute("CREATE TABLE historicalData (symbol text, date text, date_index real, open real, high real, low real, close real, volume real, count real, WAP real)")
	c.execute("CREATE TABLE ? (testField text)", [tableName])

def dropTable(tableName):
	c.execute("drop table ?", [tableName])

def getTableList():
	c.execute("select name from sqlite_master where type='table'")

def addRow(rowContents): #format = (column1 type1, column2 type2)

	# Insert a row of data
	#c.execute("INSERT INTO historicalData VALUES (date=20160303, open=68.97, high=69.66, low=68.69, close=69.66, volume=21072, count=13171, WAP=69.333)")
	c.execute("INSERT INTO testTable VALUES (?)", [rowContents])

def commit():
	# Save (commit) the changes
	conn.commit()

def close():
	# We can also close the connection if we are done with it.
	# Just be sure any changes have been committed or they will be lost.
	conn.close()

if __name__ == '__main__':
#	addRow('Mary')
#	c.execute("select * from testTable")
#	dropTable('testTable')
#	c.execute("drop table testTable")
#	addTable('newTable')
	c.execute("create table newTable (col1 text)")
	getTableList()
	print(c.fetchall())