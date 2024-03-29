from sqlalchemy import \
	Boolean, \
	CheckConstraint, \
	Column, \
	Enum, \
	ForeignKey, \
	Integer, \
	String, \
	Table, \
	text

from sqlalchemy.orm import \
	mapper, \
	relationship

from sqlalchemy.dialects.postgresql import \
	INET, \
	JSON, \
	SMALLINT, \
	TEXT, \
	TIMESTAMP

from commons.domain.models import \
	Config, \
	Host, \
	Machine, \
	Path, \
	Vulnerability, \
	VulnerabilityStatusEnum, \
	VulnerabilityType

class PublicMapper(object):
	def __init__(self, Base):
		self.Base = Base
		self.config = None
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
			self.Base,
			Column("host_id", Integer, ForeignKey("host.host_id"), nullable=False, primary_key=True),
			Column("machine_id", Integer, ForeignKey("machine.machine_id"), nullable=False, primary_key=True),
			Column("updated_dttm", TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False),
		)

		self.config = Table(
			"config",
			self.Base,
			Column("config_id", Integer, primary_key=True),
			Column("name", TEXT, nullable=False, index=True, unique=True),
			Column("config", JSON, server_default='{}', nullable=False),
			Column("updated_dttm", TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False)
		)
		mapper(Config, self.config, properties={
			"id": self.config.c.config_id,
			"name": self.config.c.name,
			"config": self.config.c.config,
			"updated_dttm": self.config.c.updated_dttm
		})

		self.host = Table(
			"host",
			self.Base,
			Column("host_id", Integer, primary_key=True),
			Column("domain", String(128), unique=True, nullable=False, index=True),
			Column("added_dttm", TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False),
			Column("access_dttm", TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False),
			Column("times_offline", SMALLINT, server_default='0', nullable=False),
			Column("updated_dttm", TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False),
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
			self.Base,
			Column("machine_id", Integer, primary_key=True),
			Column("ip", INET, unique=True, nullable=False, index=True),
			Column("institute", TEXT),
			Column("external", Boolean, nullable=False, server_default='false'),
			Column("added_dttm", TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False),
			Column("updated_dttm", TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False),
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
			self.Base,
			Column("path_id", Integer, primary_key=True),
			Column("host_id", Integer, ForeignKey(self.host.c.host_id), nullable=False),
			Column("url", TEXT, unique=True, nullable=False, index=True),
			Column("method", TEXT, nullable=False),
			Column("vars", JSON),
			Column("added_dttm", TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False),
			Column("access_dttm", TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False),
			Column("times_offline", SMALLINT, server_default='0', nullable=False),
			Column("updated_dttm", TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False),
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
			self.Base,
			Column("vulnerability_id", Integer, primary_key=True),
			Column("vulnerability_type_id", ForeignKey("vulnerability_type.vulnerability_type_id"), nullable=False),
			Column("status", Enum(VulnerabilityStatusEnum), nullable=False),
			Column("found_by", TEXT, nullable=False),
			Column("found_dttm", TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False),
			Column("confirmed_by", TEXT),
			Column("confirmed_dttm", TIMESTAMP(timezone=True)),
			Column("solved_dttm", TIMESTAMP(timezone=True)),
			Column("host_id", Integer, ForeignKey(self.host.c.host_id), nullable=True),
			Column("path_id", Integer, ForeignKey(self.path.c.path_id), nullable=True),
			Column("machine_id", Integer, ForeignKey(self.machine.c.machine_id), nullable=True),
			Column("updated_dttm", TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False),
			CheckConstraint('''
				( CASE WHEN host_id IS NULL THEN 0 ELSE 1 END
				+ CASE WHEN path_id IS NULL THEN 0 ELSE 1 END
				+ CASE WHEN machine_id IS NULL THEN 0 ELSE 1 END
				) > 0'''
			),
		)
		mapper(Vulnerability, self.vulnerability, properties={
			"id": self.vulnerability.c.vulnerability_id,
			"type": relationship(VulnerabilityType),
			"status": self.vulnerability.c.status,
			"found_by": self.vulnerability.c.found_by,
			"found_dttm": self.vulnerability.c.found_dttm,
			"confirmed_by": self.vulnerability.c.confirmed_by,
			"confirmed_dttm": self.vulnerability.c.confirmed_dttm,
			"solved_dttm": self.vulnerability.c.solved_dttm,
			"host": relationship(Host),
			"path": relationship(Path),
			"machine": relationship(Machine),
			"updated_dttm": self.vulnerability.c.updated_dttm
		})

		self.vulnerability_type = Table(
			"vulnerability_type",
			self.Base,
			Column("vulnerability_type_id", Integer, primary_key=True),
			Column("name", TEXT, unique=True, nullable=False, index=True),
			Column("description", TEXT),
			Column("severity", SMALLINT, nullable=False, index=True),
			Column("updated_dttm", TIMESTAMP(timezone=True), server_default=text('now()'), nullable=False),
		)
		mapper(VulnerabilityType, self.vulnerability_type, properties={
			"id": self.vulnerability_type.c.vulnerability_type_id,
			"name": self.vulnerability_type.c.name,
			"description": self.vulnerability_type.c.description,
			"severity": self.vulnerability_type.c.severity,
			"updated_dttm": self.vulnerability_type.c.updated_dttm
		})
