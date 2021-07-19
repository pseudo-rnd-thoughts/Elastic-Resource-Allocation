qsub -v file='alibaba',model_file='alibaba',num_tasks='30',num_servers='6',extra='model scaling' run_script.sh
qsub -v file='alibaba',model_file='alibaba',num_tasks='500',num_servers='6',extra='task sizing' run_script.sh
qsub -v file='alibaba',model_file='alibaba',num_tasks='500',num_servers='6',extra='server sizing' run_script.sh

qsub -v file='greedy',model_file='alibaba',num_tasks='10',num_servers='2',extra='elastic optimal' run_script.sh
qsub -v file='greedy',model_file='alibaba',num_tasks='15',num_servers='3',extra='relaxed optimal' run_script.sh
qsub -v file='greedy',model_file='alibaba',num_tasks='20',num_servers='4',extra='relaxed optimal' run_script.sh
qsub -v file='greedy',model_file='alibaba',num_tasks='30',num_servers='6',extra='non-elastic optimal' run_script.sh
qsub -v file='greedy',model_file='alibaba',num_tasks='30',num_servers='6',extra='greedy' run_script.sh
qsub -v file='greedy',model_file='alibaba',num_tasks='40',num_servers='8',extra='greedy' run_script.sh

qsub -v file='greedy',model_file='alibaba',num_tasks='80',num_servers='16',extra='greedy' run_script.sh
qsub -v file='greedy',model_file='alibaba',num_tasks='160',num_servers='32',extra='greedy' run_script.sh

qsub -v file='alibaba',model_file='alibaba',num_tasks='10',num_servers='2',extra='foreknowledge elastic' run_script.sh
qsub -v file='alibaba',model_file='alibaba',num_tasks='15',num_servers='3',extra='foreknowledge non-elastic' run_script.sh
qsub -v file='alibaba',model_file='alibaba',num_tasks='20',num_servers='4',extra='foreknowledge non-elastic' run_script.sh
qsub -v file='alibaba',model_file='alibaba',num_tasks='30',num_servers='6',extra='foreknowledge non-elastic' run_script.sh

qsub -v file='resource_ratio',model_file='alibaba',num_tasks='30',num_servers='6',extra='non-elastic optimal' run_script.sh
qsub -v file='resource_ratio',model_file='alibaba',num_tasks='30',num_servers='6',extra='time limited' run_script.sh
qsub -v file='resource_ratio',model_file='alibaba',num_tasks='20',num_servers='4',extra='non-elastic optimal' run_script.sh

qsub -v file='online',model_file='alibaba',num_servers='4' run_script.sh
qsub -v file='online',model_file='alibaba',num_servers='6' run_script.sh
qsub -v file='online',model_file='alibaba',num_servers='4',extra='greedy' run_script.sh
qsub -v file='online',model_file='alibaba',num_servers='6',extra='greedy' run_script.sh
