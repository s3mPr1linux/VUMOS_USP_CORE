from sqlalchemy import \
	Boolean, \
	Column, \
	Enum, \
	ForeignKey, \
	Integer, \
	MetaData, \
	String, \
	Table, \
	TEXT

from sqlalchemy.orm import \
	mapper, \
	relationship

from sqlalchemy.dialects.postgresql import \
	INET, \
	JSON, \
	SMALLINT, \
	TEXT, \
	TIMESTAMP

from domain.models import \
	Host, \
	Path, \
	Machine

Base = MetaData()

class Mapper(object):
	def __init__(self):
		self.host = None
		self.machine = None
		self.machine_host = None
		self.path = None
		self.vulnerability = None
		self.vulnerability_type = None
		self.map()

	def map(self):
		self.machine_host = Table(
			"machine_host",
			Base,
			Column("host_id", Integer, ForeignKey("host.host_id"), nullable=False, primary_key=True),
			Column("machine_id", Integer, ForeignKey("machine.machine_id"), nullable=False, primary_key=True),
			Column("updated_dttm", TIMESTAMP, server_default='now()', nullable=False),
		)

		self.host = Table(
			"host",
			Base,
			Column("host_id", Integer, primary_key=True),
			Column("domain", String(128), unique=True, nullable=False, index=True),
			Column("added_dttm", TIMESTAMP, server_default='now()', nullable=False),
			Column("access_dttm", TIMESTAMP, server_default='now()', nullable=False),
			Column("times_offline", SMALLINT, server_default='0', nullable=False),
			Column("updated_dttm", TIMESTAMP, server_default='now()', nullable=False),
		)
		mapper(Host, self.host, properties={
			"id": self.host.c.host_id,
			"domain": self.host.c.domain,
			"machines": relationship(Machine, secondary=self.machine_host, back_populates="hosts"),
			"added_dttm": self.host.c.added_dttm,
			"access_dttm": self.host.c.access_dttm,
			"times_offline": self.host.c.times_offline,
			"updated_dttm": self.host.c.updated_dttm
		})

		self.machine = Table(
			"machine",
			Base,
			Column("machine_id", Integer, primary_key=True),
			Column("ip", INET, unique=True, nullable=False, index=True),
			Column("institute", TEXT),
			Column("external", Boolean, nullable=False, server_default='false'),
			Column("updated_dttm", TIMESTAMP, server_default='now()', nullable=False),
		)
		mapper(Machine, self.machine, properties={
			"id": self.machine.c.machine_id,
			"ip": self.machine.c.ip,
			"hosts": relationship(Host, secondary=self.machine_host, back_populates="machines"),
			"external": self.machine.c.external,
			"institute": self.machine.c.institute,
			"updated_dttm": self.machine.c.updated_dttm
		})

		self.path = Table(
			"path",
			Base,
			Column("path_id", Integer, primary_key=True),
			Column("host_id", Integer, ForeignKey(self.host.c.host_id), nullable=False),
			Column("url", TEXT, unique=True, nullable=False, index=True),
			Column("method", TEXT, nullable=False),
			Column("vars", JSON),
			Column("added_dttm", TIMESTAMP, server_default='now()', nullable=False),
			Column("access_dttm", TIMESTAMP, server_default='now()', nullable=False),
			Column("times_offline", SMALLINT, server_default='0', nullable=False),
			Column("updated_dttm", TIMESTAMP, server_default='now()', nullable=False),
		)
		mapper(Path, self.path, properties={
			"id": self.path.c.path_id,
			"url": self.path.c.url,
			"host": relationship(Host),
			"method": self.path.c.method,
			"vars": self.path.c.vars,
			"access_dttm": self.path.c.access_dttm,
			"times_offline": self.path.c.times_offline,
			"updated_dttm": self.path.c.updated_dttm
		})

		self.vulnerability = Table(
			"vulnerability",
			Base,
			Column("vulnerability_id", Integer, primary_key=True),
			Column("vulnerability_type_id", ForeignKey("vulnerability_type.vulnerability_type_id"), nullable=False),
			Column("status", Enum("found", "confirmed", "solved", "false positive", name="vulnerability_status_enum"), nullable=False),
			Column("found_by", TEXT, nullable=False),
			Column("found_dttm", TIMESTAMP, server_default='now()', nullable=False),
			Column("confirmed_by", TEXT),
			Column("confirmed_dttm", TIMESTAMP),
			Column("solved_dttm", TIMESTAMP),
			Column("host_id", Integer, ForeignKey(self.host.c.host_id), nullable=False),
			Column("path_id", Integer, ForeignKey(self.path.c.path_id), nullable=False),
			Column("machine_id", Integer, ForeignKey(self.machine.c.machine_id), nullable=False),
			Column("updated_dttm", TIMESTAMP, server_default='now()', nullable=False),
		)

		self.vulnerability_type = Table(
			"vulnerability_type",
			Base,
			Column("vulnerability_type_id", Integer, primary_key=True),
			Column("name", TEXT, unique=True, nullable=False, index=True),
			Column("description", TEXT),
			Column("severity", SMALLINT, nullable=False, index=True),
			Column("updated_dttm", TIMESTAMP, server_default='now()', nullable=False),
		)

Mapper()