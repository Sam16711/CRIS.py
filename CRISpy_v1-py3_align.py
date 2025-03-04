from __future__ import division
import os
import glob
import sys
import csv
from collections import Counter
from collections import OrderedDict
import pandas as pd 
import copy


#CRIS.py

#Modify parameters below in the get_parameters() section.

def get_parameters():
    #Note to user- Change text inside of quote marks ('YOUR DNA SEQUENCES GO HERE') for your experiment.  Case of text does not matter.
    ID = 'Locus_1_w_align'
    ref_seq = str.upper('agggaatgccccggagggcggagaactgggacgaggccgaggtaggcgcggaggaggcaggcgtcgaagagtacggccctgaagaagacggcggggaggagtcgggcgccgaggagtccggcccggaagagtccggcccggaggaactgggcgccgaggaggagatgg')
    seq_start = str.upper('GCGGAGAACTG')
    seq_end = str.upper('GCCGAGGAGGA')
    fastq_files = '*.fastq'
    test_list = [
               str('g10'),   str.upper('GAGGCAGGCGTCGAAGAGTACGG'), 
               str('g14'),   str.upper('CGGCCCTGAAGAAGACGGCGGGG'),
               str('g6'),   str.upper('CCGAGGAGTCCGGCCCGGAAGAG'),
                ]

    return ID,ref_seq,seq_start,seq_end,fastq_files,test_list


def pairwise(iterable):
    #Make an ordered dictionary from items in in test list
    "s -> (s0, s1), (s2, s3), (s4, s5), ..."
    a = iter(iterable)
    return zip(a, a)


def make_project_directory(save_dir):
    #Create a project directory to store files in
    cwd = os.getcwd()   #Get current working directory
    try:
        os.stat(save_dir)
    except:
        os.mkdir(save_dir)

def write_to_file(record_entry,f):
    #Writes results to the results_counter.txt file.  Method of inserting space between each well to make the .txt file easier to read.  Based on # of items in well list
    f.write("\n")
    for record in record_entry:         #record entry is a giant list (master_Record) that contains well-lists as elements
        for line in record:
            if len(record) > 2:
                f.write(str(line) + '\n')
            else:
                pass
        if len(line) > 2:
            f.write('\n\n') 
        else:
            pass        

def make_counter(indel_size_list, current_fastq_file, dict_Counters, c_Counter, SNP_test, raw_wt_counter):
    top_common = 12             #Number of top found reads to write to results_counter .txt file
    temp_counter = Counter(indel_size_list).most_common(top_common)    #Count top indels present in fastq file
    temp_dict =OrderedDict()                                           
    #If there are not a total of at least 'top_common' common reads from the summary file, fill the spaces with NA, NA
    if len(Counter(indel_size_list).most_common(top_common)) <top_common:
            for i in range (0,top_common - len(Counter(indel_size_list).most_common(top_common))):
                temp_counter.append(("NA","NA"))
            else:
                pass
    temp_dict['Name']=str(current_fastq_file)              #Fill in Name column of CSV file with the file fastq name
    temp_dict['Sample']=''                                 #Makes a blank column for user to fill in sample names
    counter =1
    
    for k in dict_Counters:
        try:
            temp_dict[k] = str( str(dict_Counters[k]) + ' (' + str(format((dict_Counters[k] / c_Counter*100), '.1f')) + '%)')
            temp_dict[str('%'+ k)] = str(format((dict_Counters[k] / c_Counter)*100, '.1f'))
            temp_dict['Total'] = c_Counter
            temp_dict['SNP_test'] = SNP_test
            temp_dict['raw_wt_counter'] = raw_wt_counter
            temp_dict['Total_indel'] = str((format(((c_Counter - indel_size_list.count(0))/c_Counter)*100,'.1f')))
        except ZeroDivisionError:
            pass
        
    for k,g in temp_counter:        #Fill in top indels sizes and amount
        temp_dict['#'+ str(counter)+ '-Indel']=k
        try:
          # temp_dict['z%Indel'+str(counter)]= format(g/c_Counter *100, '.1f')
           temp_dict['#'+ str(counter)+'-Reads(%)'] = str(g) + ' ('+ str(format(g/c_Counter*100, '.1f')) + '%)'
        except TypeError:
            pass
        counter+=1
    return temp_dict
    


def search_fastq(ID,ref_seq,seq_start,seq_end,fastq_files,test_list):
    #Process the fastq file and look for reads
    test_dict=OrderedDict()                  #Name, Sequence of each item that is being searched for           
    dict_Counters = OrderedDict()            #Name, Count of each item in the dictionary being searched for (ie current_fastq_file)
    master_distance_and_count_summary =[]
    save_dir = os.getcwd()+"/"+ str(ID) + "/"   
    fastq_counter = 0               #Count the number of fastq_files with reads
    master_Record = []             #Master list, Master list contains lists
    indel_size_list = []             #list of indel sizes found in the fastq.  For each read, one indel size is recorded
    csv_summary_df = pd.DataFrame()
    master_distance_and_count_summary =[]

    for x,y in pairwise(test_list):          #Create an ordered dictionary of items in test_list
        test_dict[x] = y
    save_dir = os.getcwd()+"/"+ str(ID) + "/"
    print("Working directory: {}".format(str(os.getcwd())))#save_dir
    make_project_directory(save_dir)
    file_name = save_dir+'results_counter ' + ID + '.txt'
    f = open(file_name, "w")
    wt_distance = ref_seq.find(seq_end)+len(seq_end) - ref_seq.find(seq_start)      #Expected size of WT read, the distance between the two anchor points made from seq_start and seq_end
    f.write(ID + '\n')
    f.write(str("seq_start: "+seq_start+'\n'))    
    f.write(str("seq_end: "+seq_end+'\n'))
    f.write("Test_Sequences: \n")
    for key, value in test_dict.items():                #Go through the test_dict and write each item that is being searched for
        f.write(str(key)+": "+value+'\n')
        print(key, value)
        dict_Counters[str(key)]=0
        
    print('Expected WT distance: {}'.format(wt_distance))     #The expected distance between  seq_start and seq_end if the DNA is WT/ REF
    if wt_distance < 0:
        f.write("\n\n WARNING: THIS IS NOT GOING TO GIVE YOU THE FULL DATA. YOUR EXPECTED WT DISTANCE IS LESS THAN 0, it is: {}\n  Check your seq_start and seq_end again\n".format(wt_distance))

    print("Program Running")

    for each_fastq_file in glob.glob(fastq_files):   #For each clone (really each fastq file in directory), open the file as "clone"
        c_Counter = 0                     #Reset control counter to 0, this counter counts how many times both seq_start and seq_end are found in a line.
        start_counter = 0                  #How many times seq_start is found in a fastq file, used for SNP check
        end_counter = 0                    #How many times seq_end is found in a fastq file, used for SNP check
        raw_wt_counter=0                   #Calculate how many times first item in test_list is found in fastqfile, a check for SNPs
        for items in test_dict:            # RESET DICT COUNTERS TO 0
            dict_Counters[str(items)]=0
        indel_size_list = []                          #List of all the indel sizes found in each file
        fastq_name = str(each_fastq_file)                                #Well name that contains the clone being screened
        line_list =[]                                  #List of all the lines found in a fastq file.  These lines must contain both seq_start and seq_end.  Used to find most highly occuring sequences
        current_fastq_file = open(str(each_fastq_file), "r")    

        line_counter = 0
        for line in current_fastq_file:   #For each line in the fastq file
            line_counter+=1
            if line_counter % 4 != 2: # Only parse the lines that contain the dna sequences
                continue
            first_item = list(test_dict.items())[0][1] #Counts the number of times the first item in test_dict is found in ANY of the lines of the fastq file.  This is a check in case SNPs are in BOTH seq_start and seq_end
            if line.find(first_item) > 0:
                raw_wt_counter+=1
            read_start_ind = line.find(seq_start)
            read_end_ind = line.find(seq_end)
            if read_start_ind > 0 and read_end_ind > 0:
                c_Counter += 1
                start_counter +=1     #Count # of times seq_start is found
                end_counter +=1       #Count # of times seq_end is found
                indel_size = read_end_ind+len(seq_end) - read_start_ind - wt_distance
                indel_size_list.append(indel_size)
                line_list.append(line[read_start_ind:read_end_ind])
                for item in test_dict:
                    if test_dict[item] in line:
                        dict_Counters[item] +=1
            
            #elif line.find(seq_start)>0 and line.find(seq_end)<0:        #If seq_start is found and seq_end is not found, for SNPT test
            elif read_start_ind > 0 and read_end_ind < 0:    
                start_counter +=1
            #elif line.find(seq_end)>0 and line.find(seq_start)<0:        #If seq_end is found and seq_start is not found, for SNP test
            elif read_start_ind < 0 and read_end_ind > 0:
                end_counter+=1
        
        current_fastq_file.close()               
        try:
            SNP_test = format(start_counter / end_counter, '.2f')        #Compare counts of seq_start and seq_end for SNP test
        except ZeroDivisionError:
            pass
        try:
            raw_wt_counter = str(str(raw_wt_counter) +  ' ('+ format((raw_wt_counter/ dict_Counters[list(test_dict.items())[0][0]]), '.1f') +')') #Calculate raw_wt_counter
        except ZeroDivisionError:
            pass
       

        if c_Counter > 10 :  #if more than 10 control read counts, record data
            print("{}: Total_reads:{}, {}".format(fastq_name,str(c_Counter).ljust(2), dict_Counters.items()))
            fastq_counter += 1
            test_list_string=str(" Testing: ")
            for k,v in dict_Counters.items():
                test_list_string=test_list_string+"({}:{}), ".format(k,v)
            temp = Counter(line_list).most_common(12)
            #summary_line is a list, format:  Miller-Plate13-C01 TOTAL:2072 OrderedDict([('g3', 2010), ('Block_Only', 0), ('Mod_Only', 2), ('Block_Mod', 0), ('Full', 0)])       [(0, 2070), (-1, 2)]
            summary_line = ([str(fastq_name) + " TOTAL:" + str(c_Counter)+" "+test_list_string+"     "+"Top_reads:"+ str(Counter(indel_size_list).most_common(12))])
            for k,v in temp:          #Append the top found DNA sequences to summary_line
                #print("k: ",k," v: ", v)
                summary_line.append('{} , {}'.format(k,v))
            master_Record.append(summary_line)
            master_distance_and_count_summary.append(make_counter(indel_size_list,str(fastq_name), dict_Counters, c_Counter,SNP_test,raw_wt_counter))


    print("SUMMARY")
    make_project_directory(ID)
    #print master_distance_and_count_summary
    pd_columns = ['Name','Sample','Total', 'Total_indel', '#1-Indel','#1-Reads(%)','#2-Indel','#2-Reads(%)','#3-Indel','#3-Reads(%)','#4-Indel','#4-Reads(%)','#5-Indel','#5-Reads(%)',
             '#6-Indel','#6-Reads(%)','#7-Indel','#7-Reads(%)','#8-Indel','#8-Reads(%)', 'SNP_test', 'raw_wt_counter']

    flip_dict = list(test_dict.items())   #Need to flip order of items in dictionary.  That way when they are inserted into the excel list, the order will come out correct
    flip_dict.reverse()
    flip_dict=OrderedDict(flip_dict)
    for k, v in flip_dict.items():        #Insert the items from test_dict into position 3 for the column output, after 'Total'
        pd_columns.insert(3,k)
    for k, v in test_dict.items():        #Insert the % values for test_dic at the end
        pd_columns.append(str('%'+k))
    csv_summary_df = pd.DataFrame.from_records(master_distance_and_count_summary, index='Name', columns=pd_columns)
    csv_summary_df=csv_summary_df.sort_index()
    csv_summary_df = csv_summary_df[pd.notnull(csv_summary_df['Total'])]
    try:
        csv_summary_df.to_csv(str(save_dir+ID)+'.csv')    #Filename to save csv as
    except (IOError):
        print('ERROR.  Script did not execute properly.')
        print('The requested .csv file {} is either open or you do not have access to it.  If open, please close file and rerun program').format(str(save_dir+ID)+'.csv')
        
    master_Record = sorted(master_Record)
    print("Total wells with product:", fastq_counter)
    write_to_file(master_Record,f)
    f.close()

    return master_Record, save_dir
    
def buildTable(seq1,seq2,match=1,mismatch=-1,gap_open=-50,gap_ext=-0.5):
    """Build alignment table"""
    middle = []
    upper = []
    lower = []

    # Initalize matricies for align with affine gap penalty
    for row in range(len(seq1) +1):
        rowM = []
        rowU = []
        rowL = []
        for col in range(len(seq2) + 1):
            if row == 0 and col == 0:
                rowU.append(gap_open)
                rowL.append(gap_open)
                rowM.append(0)
            elif row == 0 and col >0:
                rowL.append(-float('Inf'))
                rowU.append(gap_open + col * gap_ext)
                rowM.append(gap_open + col * gap_ext)
            elif row >0 and col == 0:
                rowL.append(gap_open + row * gap_ext)
                rowM.append(gap_open + row * gap_ext)
                rowU.append(-float('Inf'))
            else:
                rowU.append(0)
                rowL.append(0)
                rowM.append(0)

            

        middle.append(rowM)
        lower.append(rowL)
        upper.append(rowU)

    # Calculate scores
    for i in range(1,len(seq1)+1):
        for j in range(1,len(seq2)+1):
          # Calculate match/mismatch score for middle
            score = 0
            symbol_1 = seq1[i -1]
            symbol_2 = seq2[j -1]
            if symbol_1 == symbol_2:
                score = match
            else:
                score = mismatch

            # Update matricies
            lower[i][j] = max(lower[i-1][j] + gap_ext,middle[i-1][j] + gap_open +gap_ext)
            upper[i][j] = max(upper[i][j-1] + gap_ext, middle[i][j-1] + gap_open +gap_ext)
            middle[i][j] = max(lower[i][j],upper[i][j],middle[i-1][j-1] + score)
    
    align1,align2,match_symbols = traceback(seq1,seq2,lower,middle,upper,match,mismatch,gap_open,gap_ext)
    return align1,align2,match_symbols

def traceback(seq1,seq2,lower,middle,upper,match,mismatch,gap_open,gap_extend):
    align1 = ""
    align2 = ""
    match_symbols = ""

    i = len(middle) -1
    j = len(middle[0]) -1
    
    matrix = "middle"
    
    #Iterate through cells
    while i != 0 and j !=0:
        
                
        if matrix == "upper": # Extending Gap in Seq 2
            if middle[i][j-1] + gap_open + gap_extend == upper[i][j]: # Gap open
                matrix = "middle"
                
            elif upper[i][j] != upper[i][j-1] + gap_extend:
                exit("The math isn't adding up in the upper matrix. upper[{}][{}]".format(i,j))
            
            align1 = "-" + align1
            align2 = seq2[j-1] + align2
            match_symbols = " " + match_symbols
            j-=1
            
        elif matrix == "lower": # Extending Gap in Seq 1
            if middle[i-1][j] + gap_open + gap_extend == lower[i][j]: # Gap open in lower
                matrix = "middle" # End gap at gap start
            
            elif lower[i][j] != lower[i-1][j] + gap_extend:
                exit("The math isn't adding up in the lower matrix. lower[{}][{}]".format(i,j))
            
            align1 = seq1[i-1] + align1
            align2 = "-" + align2
            match_symbols = " " + match_symbols
            i-=1
            
        elif matrix == "middle": 
            if (seq1[i-1] == seq2[j-1] and middle[i][j] == middle[i-1][j-1] + match) or ( seq1[i-1] != seq2[j-1] and middle[i][j] == middle[i-1][j-1] + mismatch):
                align1 = seq1[i-1] + align1
                align2 = seq2[j-1] + align2

                if seq1[i-1] == seq2[j-1]:
                    match_symbols = "|" + match_symbols
                else:
                    match_symbols = "." + match_symbols
                i-=1
                j-=1
            
            elif middle[i][j] == lower[i][j]: # Start Traversing lower matrix. Gap in seq 1
                matrix = "lower"

            elif middle[i][j] == upper[i][j]: # Start traversing upper matrix. Gap in seq2 (i)
                matrix = "upper"

           
        # Align the rest of the sequence to gaps if row or column is index 0 ('-')
        while i != 0 and j == 0:
            align2 = "-" + align2
            align1 = seq1[i-1] + align1
            match_symbols = " " + match_symbols
            i-=1

        while i ==0 and j != 0:
            align1 = "-" + align1
            align2 = seq2[j-1] + align2
            match_symbols = " " + match_symbols
            j-=1
    
    return align1,align2,match_symbols

def print_table(t):
  for c, row in enumerate(t):
    for col in row:
      print("{0:>5}".format(col),end="")
    print("\n",end="")

def write_alignments(alignL,ID,outDir,outF="alignments.txt"):
    outPath = os.path.join(outDir,ID+outF)
    with open(outPath,"w") as OF:
        for line in alignL:
            outString = " ".join(line)
            print(outString,file=OF)

def get_kmers(seq,k):
    """ Breaks seq down into list of kmers """
    kmers = []
    for i in range(len(seq)-k +1):
        kmers.append(seq[i:i+k])

    
    return kmers

def find_5prime_seq_diff(ref,seq):
    """ Finds first bp difference btween ref and seq.
        Returns index where difference found """

    for i in range(len(ref)):
        ref_bp = ref[i]
        seq_bp = seq[i]

        if ref_bp != seq_bp:
            return i

    return None

def find_3prime_seq_diff(ref_seq):
    """ Finds first bp difference starting from the 3' end
        bewtween the ref and seq (read). Returns index where 
        diff found"""

    for i in range(len(ref)-1,-1,-1):
        ref_bp = ref[i]
        seq_bp = seq[i]

        if ref_bp != seq_bp:
            return i

    return None

def main():
    ID = ''
    ref_seq = ''
    seq_start = ''
    seq_end = ''
    fastq_files = ''
    test_list = []
    print("CRIS.py \nMain program")
    ID, ref_seq, seq_start, seq_end, fastq_files, test_list = get_parameters()
    master_record, save_dir = search_fastq(ID, ref_seq, seq_start, seq_end, fastq_files, test_list)

    # Align indels to ref seq provided
    print('Aligning Indels')
    comparison_start = ref_seq.find(seq_start)
    comparison_end = ref_seq.find(seq_end)
    ref_seq_adj = ref_seq[comparison_start:comparison_end]
    
    alignmentList = []
    for record in master_record:
        header = record[0]
        alignmentList.append([header])
        for j in range(1,len(record)):
            read_seq, read_count = record[j].split(",")
            read_seq = read_seq.strip() # Split extra whitepace from indel
            diff_5 = find_5prime_seq_diff(ref_seq_adj,read_seq)
            
            
            if diff_5 == None: # Exact match between ref_seq and read_seq
                align1 = ref_seq_adj
                align2 = read_seq
                match_symbols = "|" * len(ref_seq_adj)
            
            diff_3 = find_3prime_seq_diff(ref_seq_adj, read_seq)
            
            # Adjust sequences to where mismatches start between ref_seq and read_seq
            # This makes alignment faster as alignment takes O(mn) time
            ref_seq_adj_short = ref_seq_adj[diff_5-1:diff_3+1]
            read_seq_short = read_seq[diff_5-1:diff_3+1]
            align1,align2,match_symbols = buildTable(ref_seq_adj_short,read_seq_short)
            alignment = ref_seq_adj[:diff_5-1] + align1 + "\n" + match_symbols + "\n" + align2 + ref_seq_adj[diff_3+2:]
            alignmentList.append([alignment, read_count])

    write_alignments(alignmentList,ID,save_dir)
    print("Done")
if __name__== "__main__":
    main()
