with open("app/database.py", "r") as f:
    text = f.read()

migration_sql = """                    DO $$
                    BEGIN
                        IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sessionstatus') THEN
                            ALTER TYPE sessionstatus ADD VALUE IF NOT EXISTS 'STARTING';
                        END IF;
                        
                        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'attack_sessions') THEN
                            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'attack_sessions' AND column_name = 'submission_attempts') THEN
                                ALTER TABLE attack_sessions ADD COLUMN submission_attempts INTEGER DEFAULT 0 NOT NULL;
                            END IF;
                        END IF;
                    END $$;"""

text = text.replace("""                    DO $$
                    BEGIN
                        IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'sessionstatus') THEN
                            ALTER TYPE sessionstatus ADD VALUE IF NOT EXISTS 'STARTING';
                        END IF;
                    END $$;""", migration_sql)

with open("app/database.py", "w") as f:
    f.write(text)

