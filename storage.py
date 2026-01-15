import sqlite3

class MessageStore:
    def __init__(self, conn):
        self.conn = conn

    def insert_message(self, msg):
        try:
            self.conn.execute(
                "INSERT INTO messages VALUES (?,?,?,?,?,?)",
                (
                    msg["message_id"],
                    msg["from"],
                    msg["to"],
                    msg["ts"],
                    msg.get("text"),
                    msg["created_at"],
                ),
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def list_messages(self, limit, offset, from_, since, q):
        where, params = [], []

        if from_:
            where.append("from_msisdn = ?")
            params.append(from_)
        if since:
            where.append("ts >= ?")
            params.append(since)
        if q:
            where.append("LOWER(text) LIKE ?")
            params.append(f"%{q.lower()}%")

        where_sql = f"WHERE {' AND '.join(where)}" if where else ""

        total = self.conn.execute(
            f"SELECT COUNT(*) FROM messages {where_sql}", params
        ).fetchone()[0]

        rows = self.conn.execute(
            f"""
            SELECT message_id, from_msisdn, to_msisdn, ts, text
            FROM messages
            {where_sql}
            ORDER BY ts ASC, message_id ASC
            LIMIT ? OFFSET ?
            """,
            (*params, limit, offset),
        ).fetchall()

        data = [
            {
                "message_id": r[0],
                "from": r[1],
                "to": r[2],
                "ts": r[3],
                "text": r[4],
            }
            for r in rows
        ]
        return data, total

    def stats(self):
        cur = self.conn.cursor()
        total = cur.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        senders = cur.execute(
            """
            SELECT from_msisdn, COUNT(*) c
            FROM messages
            GROUP BY from_msisdn
            ORDER BY c DESC
            LIMIT 10
            """
        ).fetchall()

        first_ts = cur.execute("SELECT MIN(ts) FROM messages").fetchone()[0]
        last_ts = cur.execute("SELECT MAX(ts) FROM messages").fetchone()[0]

        return {
            "total_messages": total,
            "senders_count": len(senders),
            "messages_per_sender": [
                {"from": s[0], "count": s[1]} for s in senders
            ],
            "first_message_ts": first_ts,
            "last_message_ts": last_ts,
        }
