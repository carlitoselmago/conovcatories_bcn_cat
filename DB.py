import psycopg2
import os

class DB():

    def __init__(self):
        self.pg_connect()


    def pg_connect(self):
        """Connect to PostgreSQL using env vars PGUSER and PGPASSWORD."""
        
        self.pg_conn = psycopg2.connect(
            dbname="convos",
            user=os.environ.get("PGUSER"),
            password=os.environ.get("PGPASSWORD"),
            host="localhost",
            port=5432
        )
        self.pg_cursor = self.pg_conn.cursor()
        print("✓ Connected to PostgreSQL")
    
    def pg_execute(self, sql, params=None, fetch=False):
        """
        Execute INSERT/UPDATE/DELETE.
        If fetch=True, return fetched rows (e.g. for RETURNING).
        Otherwise return True/False.
        """
        if self.pg_conn is None:
            self.pg_connect()

        try:
            self.pg_cursor.execute(sql, params)

            if fetch:
                rows = self.pg_cursor.fetchall()
                self.pg_conn.commit()
                return rows

            self.pg_conn.commit()
            return True

        except Exception as e:
            print("⚠ PostgreSQL execute error:", e, sql, params)
            self.pg_conn.rollback()
            return None if fetch else False

    def get_col_names(self):
        column_names = [desc[0] for desc in self.pg_cursor.description]
        return column_names

    def pg_query(self, sql, params=None):
        """
        Execute SELECT and return all rows.
        """
        if self.pg_conn is None:
            self.pg_connect()

        try:
            self.pg_cursor.execute(sql, params)
            return self.pg_cursor.fetchall()

        except Exception as e:
            print("⚠ PostgreSQL query error:", e, sql, params)
            self.pg_conn.rollback()   # ← CRUCIAL FIX
            return None


    def normalize_dni_pattern(self, dni):
        """
        Converts a DNI potentially containing '*' into a SQL LIKE pattern.
        Example: '4676****' -> '4676%%%%'
        """
        if not dni:
            return None
        if "*" not in dni:
            return dni.strip()

        return dni.replace("*", "%")

    def pg_find_artist_by_dni(self, dni):
        #print("find by dni")
        """
        Try to find an artist by exact DNI or pattern.
        """
        if not dni:
            return None

        dni = dni.strip()

        # CASE 1: full DNI (no stars)
        if "*" not in dni:
            rows = self.pg_query(
                "SELECT id, name, dni FROM artists WHERE dni = %s",
                (dni,)
            )
            return rows[0] if rows else None

        # CASE 2: masked DNI with *
        pattern = self.normalize_dni_pattern(dni)
        rows = self.pg_query(
            "SELECT id, name, dni FROM artists WHERE dni LIKE %s",
            (pattern,)
        )
        return rows[0] if rows else None
        
    def pg_find_artist_by_name(self, name, threshold=0.45):
        #print("find by name")

        rows = self.pg_query(
            """
            SELECT 
                id, 
                name, 
                dni, 
                similarity(name::text, %s::text) AS score
            FROM artists
            WHERE similarity(name::text, %s::text) >= %s
            ORDER BY score DESC
            LIMIT 1
            """,
            (name, name, threshold)
        )

        if rows:
            return rows[0]

        return None



    def add_artist(self, name, dni,iscollective):
        iscollective = bool(iscollective)
        """
        Insert artist if not previously registered.
        Tries to match by DNI first, then by fuzzy name.
        Returns: (id, existed_before)
        """
        if self.pg_conn is None:
            self.pg_connect()

        # 1. Try DNI match
        existing = self.pg_find_artist_by_dni(dni)
        if existing:
            print("✓ Artist already exists (dni match):", existing)
            return existing[0], True

        # 2. Try name match
        existing = self.pg_find_artist_by_name(name)
        if existing:
            artist_id, artist_name, artist_dni, score = existing
            print(f"✓ Artist exists (name similarity {score:.2f}): {artist_name}")
            return artist_id, True

        # 3. Insert new artist
        rows = self.pg_execute(
            "INSERT INTO artists (name, dni,iscollective) VALUES (%s, %s,%s) RETURNING id",
            (name, dni,iscollective),
            fetch=True
        )

        if not rows:
            print("⚠ Could not insert new artist.")
            return None, False

        new_id = rows[0][0]
        print("✓ New artist inserted with id:", new_id)
        return new_id, False


    def add_convocatoria(self, data):
        """
        Insert convocatoria record if not previously registered.
        Matching logic:
        - First check for exact match on (entitat, year, artist)
        Returns: (id, existed_before)
        """

        if self.pg_conn is None:
            self.pg_connect()

        entitat = data.get("entitat")
        year    = data.get("year")
        artist  = data.get("artist")
       
        project = data.get("project")
        category = data.get("category")

        # 1. Check if this convocatoria already exists
        existing = self.pg_query(
            """
            SELECT id 
            FROM convocatoria
            WHERE entitat = %s AND year = %s AND artist = %s
            """,
            (entitat, year, artist)
        )

        if existing:
            print(f"✓ Convocatoria already exists: id {existing[0][0]}")
            return existing[0][0], True

        # 2. Insert new convocatoria
        rows = self.pg_execute(
            """
            INSERT INTO convocatoria
            (artist, granted, money, year, score, reason, entitat, project, category)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
            """,
            (
                data.get("artist"),
                data.get("granted"),
                data.get("money"),
                data.get("year"),
                data.get("score"),
                data.get("reason"),
                data.get("entitat"),
                data.get("project"),
                data.get("category"),
  
            ),
            fetch=True
        )

        if not rows:
            print("⚠ Could not insert new convocatoria.")
            return None, False

        new_id = rows[0][0]
        print(f"✓ New convocatoria inserted with id: {new_id}")
        return new_id, False


    def update_artist(self, artist_id, data):
        """
        Update artist with partial information.
        """
        if not data:
            print("⚠ No fields to update.")
            return False

        if self.pg_conn is None:
            self.pg_connect()

        # Build dynamic SQL
        columns = []
        values = []

        for key, value in data.items():
            if value is None:
                continue
            columns.append(f"{key} = %s")
            values.append(value)

        if not columns:
            print("⚠ No valid fields to update.")
            return False

        values.append(artist_id)

        sql = f"""
            UPDATE artists
            SET {', '.join(columns)}
            WHERE id = %s;
        """

        ok = self.pg_execute(sql, tuple(values))
        if ok:
            print(f"✓ Artist {artist_id} updated.")
        return ok


    def pg_close(self):
        """Close PostgreSQL connection cleanly."""
        try:
            if self.pg_cursor:
                self.pg_cursor.close()
            if self.pg_conn:
                self.pg_conn.close()
            print("✓ PostgreSQL connection closed")
        except Exception as e:
            print("⚠ Error closing PostgreSQL connection:", e)