import re
from logging import Logger
from datetime import datetime
from subprocess import run, PIPE

from commons.domain.models import \
	Sqlmap, \
	Vulnerability, \
	VulnerabilityStatusEnum

from commons.domain.repository import \
	ConfigRepository, \
	SqlmapRepository, \
	VulnerabilityRepository, \
	VulnerabilityTypeRepository

class Controller(object):
	def __init__(self,
				 config_repository: ConfigRepository,
				 sqlmap_repository: SqlmapRepository,
				 vulnerability_repository: VulnerabilityRepository,
				 vulnerability_type_repository: VulnerabilityTypeRepository,
				 logger: Logger):
		self.config_repository = config_repository
		self.sqlmap_repository = sqlmap_repository
		self.vulnerability_repository = vulnerability_repository
		self.vulnerability_type_repository = vulnerability_type_repository
		self.logger = logger

	def run(self):
		config = self.config_repository.get_by_name("Sqlmap").config

		self.logger.debug(f"config = {config}")
		
		self.sqlmap_repository.add_paths_to_sqlmap()

		redo_in = config["redo_in"]

		sqlmap = self.sqlmap_repository.get_next(weeks=redo_in["weeks"], days=redo_in["days"])

		if sqlmap is None:
			return 1

		self.logger.info(f"starting sqlmap to {sqlmap.path.url}")

		self.run_sqlmap(sqlmap)
		return 0

	def run_sqlmap(self, sqlmap: Sqlmap):
		entry = sqlmap.path
		sqlmap_command = ['sqlmap', '-u']
		sqlmap_urlstring = entry.url+'?'
		for var in entry.vars:
			if re.search(r'\A9{3,}', var['value']):
				var['value'] = '1'
			if not 'type' in var: # if there is no type, its a querystring url
				sqlmap_urlstring += f"{var['name']}={var['value'] if var['value'] else 'a'}&"
		sqlmap_command.append(sqlmap_urlstring[:-1])
		sqlmap_command.append(f'--method={entry.method.lower()}')
		if entry.method.lower() != 'get':
			sqlmap_datastring = '--data='
			for var in entry.vars:
				if 'type' in var:
					sqlmap_datastring += f"{var['name']}={var['value'] if var['value'] else 'a'}&"
			sqlmap_command.append(sqlmap_datastring[:-1])
		
		sqlmap_command.append('--threads=1')
		sqlmap_command.append('--level=5')
		# sqlmap_command.append('--smart') # no, smart is actually pretty dumb
		sqlmap_command.append('--technique=BEUSTQ')
		sqlmap_command.append('--batch')
		sqlmap_command.append('--disable-coloring')
		result = run(sqlmap_command, stdout=PIPE)

		self.logger.debug(result.stdout)
		
		sql_injection = self.vulnerability_type_repository.get_by_name("SQL injection")
		vulnerability = self.vulnerability_repository.get_by(path=sqlmap.path, type=sql_injection)
		if vulnerability:
			vulnerability = vulnerability[0]
		if b'sqlmap identified the following injection point' not in result.stdout:
			sqlmap.clear = True
			sqlmap.updated_dttm = datetime.now()
			if vulnerability:
				vulnerability.status = VulnerabilityStatusEnum(3)
				vulnerability.solved_dttm = datetime.now()
				self.vulnerability_repository.update(vulnerability)
		else:
			injectable_str = result.stdout.split(b'\n---\n')[1].decode()
			parameter_reg = re.search(r'(\s*Parameter: )(.+)( \((.+)\))', injectable_str.split('\n')[0])
			output = {
				"parameter": parameter_reg[2],
				"method": parameter_reg[4],
				"techniques": [],
			}
			techniques_str = injectable_str.split('\n\n')
			for technique in techniques_str:
				output['techniques'].append({
					"type": re.search(r'(\s+Type: )(.+)', technique)[2],
					"title": re.search(r'(\s+Title: )(.+)', technique)[2],
					"payload": re.search(r'(\s+Payload: )(.+)', technique)[2],
				})
			sqlmap.output = output
			sqlmap.updated_dttm = datetime.now()
			if vulnerability:
				vulnerability.status = VulnerabilityStatusEnum(2)
				if vulnerability.confirmed_by is None:
					vulnerability.confirmed_by = 'sqlmap'
					vulnerability.confirmed_dttm = datetime.now()
				vulnerability.solved_dttm = None
				vulnerability.updated_dttm = datetime.now()
				self.vulnerability_repository.update(vulnerability)
			else:
				vulnerability = Vulnerability(
					type=sql_injection,
					status=VulnerabilityStatusEnum(2),
					found_by='sqlmap',
					found_dttm=datetime.now(),
					confirmed_by='sqlmap',
					confirmed_dttm=datetime.now(),
					path=sqlmap.path
				)
				self.vulnerability_repository.add(vulnerability)
		self.sqlmap_repository.update(sqlmap)
