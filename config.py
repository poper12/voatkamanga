env_vars = {
  # Get From my.telegram.org
  "API_HASH": "057fd0be9d7c38526b143c582bceb24b",
  # Get From my.telegram.org
  "API_ID": "20445873",
  #Get For @BotFather
  "BOT_TOKEN": "7903390136:AAE-OflUbBwhiQI8aLGBH8ZtFsh_SaWBaDI",
  # Get For tembo.io
  "DATABASE_URL_PRIMARY": "postgresql://postgres:4NQDGksWwMhyfcP5@delicately-purposeful-hen.data-1.apse1.tembo.io:5432/postgres",
  # Logs Channel Username Without @
  "CACHE_CHANNEL": "Dump2075",
  # Force Subs Channel username without @
  "CHANNEL": "Manga_Campus",
  # {chap_num}: Chapter Number
  # {chap_name} : Manga Name
  # Ex : Chapter {chap_num} {chap_name} @Manhwa_Arena
  "FNAME": "[MC] [{chap_num}] {chap_name} @Manga_Campus"
}

dbname = env_vars.get('DATABASE_URL_PRIMARY') or env_vars.get('DATABASE_URL') or 'sqlite:///test.db'

if dbname.startswith('postgres://'):
    dbname = dbname.replace('postgres://', 'postgresql://', 1)
    
