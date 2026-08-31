/////////////////////////////////////////////////////////////////////////////////////////////
// Project Title    : Customized Virtual File System (CVFS)
// Description      : Custom implementation of a Virtual File System (VFS) 
//                    that simulates the core functionality of the Linux file System.
//                      *Practical knowledge of data structures used in OS ---
//	                    1.Inode Management
//	                    2.Super Block
//	                    3.File Tables
//	                    4.User File Descriptor Table (UFDT)
//	                    5.UAREA
//                      *Implementation of internal working of system calls
//                      (open,close,read,write,ls,stat,unlink)
//
// Date:            1/08/2026
// Author:          Snehal Sawant  
///////////////////////////////////////////////////////////////////////////////////////////////

//////////////////////////////////////////////////////
//
//  Header Files Inclusion
//
//////////////////////////////////////////////////////

#include<stdio.h>
#include<stdlib.h>
#include<unistd.h>
#include<fcntl.h>
#include<string.h>
#include<stdbool.h>

//////////////////////////////////////////////////////
//
//  User Defined Macros
//
//////////////////////////////////////////////////////

#define MAXINODE 10
#define MAXFILESIZE 1024
#define MAXOPENFILES 10

#define READ 1
#define WRITE 2
#define EXECUTE 4

#define START 0
#define CURRENT 1
#define END 2

#define EXECUTE_SUCCESS 0
#define EXECUTE_FAILURE -1

#define END_OF_FILE_REACHED 5

#define REGULARFILE 1               //Used this macro for type of file
#define SPECIALFILE 2

#define BACKUP_PATH "C:\\Users\\SAI\\Desktop\\LB\\Projects\\File-Handling-Projects\\CVFS\\Backup\\"

//////////////////////////////////////////////////////
//
//  User Defined Macros for error handling
//
//////////////////////////////////////////////////////

#define ERR_INVALID_PARAMETER -1

#define ERR_NO_INODES -2

#define ERR_FILE_ALREADY_EXIST -3
#define ERR_FILE_NOT_EXIST -4

#define ERR_PERMISSION_DENIED -5

#define ERR_INSUFFICIENT_SPACE -6
#define ERR_INSUFFICIENT_DATA -7

#define ERR_MAX_FILES_OPEN -8
#define ERR_FILE_NOT_OPEN -9

//////////////////////////////////////////////////////
//
//  Structure Name  : BootBlock
//  Description     : It holds the information to
//                    boot the operating system
//
//////////////////////////////////////////////////////

struct BootBlock
{
    char Information[100];
};

//////////////////////////////////////////////////////
//
//  Structure Name  : SuperBlock
//  Description     : It holds the information of
//                    complete file system
//
//////////////////////////////////////////////////////

struct SuperBlock
{
    int TotalInodes;
    int FreeInodes;         //When a new file is created then FreeInodes-- and when a file is deleted then FreeInodes++
};

//////////////////////////////////////////////////////
//
//  Structure Name  : Inode
//  Description     : It holds the information of file
//
//////////////////////////////////////////////////////

#pragma pack(1)
struct Inode                // 1 Inode from DILB
{
    char FileName[20];      //In actual OS the filename is stored in a separate directory file
    int InodeNumber;
    int FileSize;           //The size of complete file that can be stored in the file system
    int ActualFileSize;     //The size of actual data that is stored in the file
    int FileType;           // 1 -> Regular File, 2 -> Special File
    int ReferenceCount;     //How many times the file is opened
    int Permission;         // 1 -> Read, 2 -> Write, 3 -> Read + Write
    char *Buffer;           //Points to actual data written in the file
    struct Inode *next;     //Self referential pointer
};

typedef struct Inode INODE;
typedef struct Inode* PINODE;
typedef struct Inode** PPINODE;


//////////////////////////////////////////////////////
//
//  Structure Name  : FileTable
//  Description     : It holds the information of 
//                    only opened files
//
//////////////////////////////////////////////////////

# pragma pack(1)
struct FileTable            //File Table is created whenever a file is created and stored in UFDT 
{
    int ReadOffset;         //From where it will start reading
    int WriteOffset;        //Where it is writing
    int Mode;               //In which mode file is opened eg - read or write or both read and write
    PINODE ptrinode;        //pointer to Inode structure
};

typedef struct FileTable FILETABLE;
typedef struct FileTable* PFILETABLE;

//////////////////////////////////////////////////////
//
//  Structure Name  : UAREA
//  Description     : It holds the information of 
//                    process
//
//////////////////////////////////////////////////////

struct UAREA    
{
    char ProcessName[20];
    PFILETABLE UFDT[MAXOPENFILES];       // How many files get opened
};

//////////////////////////////////////////////////////
//
//     Global variables used in the project
//
//////////////////////////////////////////////////////

struct BootBlock bootobj;               //In C we have to mention the struct keyword to create the obj
struct SuperBlock superobj;             //In C++ we can create the object without struct keyword
struct UAREA uareaobj;

PINODE head = NULL;                     //Initializing globally is a bad programming practice but
                                        //we are doing it here for simplicity of the project

//////////////////////////////////////////////////////
//
//  Function Name : InitialiseUAREA()
//  Description   : It is used to initialise UAREA
//  Author        : Snehal Sawant
//  Date          : 31/07/2026
//
//////////////////////////////////////////////////////

void InitialiseUAREA()
{
    int i = 0;

    strcpy(uareaobj.ProcessName, "Myexe");

    for(i = 0; i < MAXOPENFILES; i++)
    {
        uareaobj.UFDT[i] = NULL;
    }

    printf("Marvellous CVFS : UAREA gets initialised successfully\n");
}

//////////////////////////////////////////////////////
//
//  Function Name : InitialiseSuperBlock()
//  Description   : It is used to initialise Super Block
//  Author        : Snehal Sawant
//  Date          : 31/07/2026
//
//////////////////////////////////////////////////////

void InitialiseSuperBlock()
{
    superobj.TotalInodes = MAXINODE;
    superobj.FreeInodes = MAXINODE;

    printf("Marvellous CVFS : Super Block gets initialised successfully\n");
}

//////////////////////////////////////////////////////
//
//  Function Name : CreateDILB()
//  Description   : It is used to create linked list of inodes
//  Author        : Snehal Sawant
//  Date          : 31/07/2026
//
//////////////////////////////////////////////////////


void CreateDILB()
{
    PINODE temp = NULL;
    PINODE newn = NULL;
    
    int i = 0;
    
    temp = head;

    for(i = 1; i <= MAXINODE; i++)
    {
        newn = (PINODE)malloc(sizeof(INODE));

        newn->InodeNumber = i;
        strcpy(newn->FileName,"\0");
        newn->FileSize = 0;
        newn->ActualFileSize = 0;
        newn->FileType = 0;
        newn->ReferenceCount = 0;
        newn->Permission = 0;
        newn->Buffer = NULL;
        newn->next = NULL;

        if(temp == NULL)
        {
            head = newn;
            temp = head;
        }
        else
        {
            temp->next = newn;
            temp = temp->next;
        }
    }
    printf("Marvellous CVFS : DILB gets created successfully\n");
}

//////////////////////////////////////////////////////
//
//  Function Name : StartAuxillaryDataInitialisation()
//  Description   : It is used to call all functions 
//                  which are used to initialise auxillary data
//  Author        : Snehal Sawant
//  Date          : 31/07/2026
//
//////////////////////////////////////////////////////


void StartAuxillaryDataInitialisation()
{
    strcpy(bootobj.Information,"Booting process of Marvellous CVFS is completed.");

    printf("%s\n",bootobj.Information);

    InitialiseUAREA();
    
    InitialiseSuperBlock();

    CreateDILB();
}

//////////////////////////////////////////////////////
//
//  Function Name : DisplayHelp()
//  Description   : It is used to display help to 
//                  the user of project
//  Author        : Snehal Sawant
//  Date          : 01/08/2026
//
//////////////////////////////////////////////////////

void DisplayHelp()
{
    printf("----------------------------------------------------------\n");
    printf("-----------------Marvellous CVFS Help Page----------------\n");
    printf("----------------------------------------------------------\n");
    
    printf("man     : It is used to display the manual page\n");
    printf("clear   : It is used to clear the terminal screen\n");
    printf("creat   : It is used to create new regular file\n");
    printf("open    : It is used to open the regular file\n");
    printf("close   : It is used to close the regular file\n");
    printf("write   : It is used to write the data into the file\n");
    printf("read    : It is used to read the data from the file\n");
    printf("stat    : It is used to display statistical information of the file\n");
    printf("unlink  : It is used to delete the file\n");
    printf("exit    : It is used to terminate Marvellous CVFS\n");
    
    printf("----------------------------------------------------------\n");
}

//////////////////////////////////////////////////////
//
//  Function Name : ManPageDisplay()
//  Description   : It is used to display 
//                  man page of specific command
//  Input         : Name of Command
//  Author        : Snehal Sawant
//  Date          : 01/08/2026
//
//////////////////////////////////////////////////////


void ManPageDisplay(char Name[])
{
    if(strcmp(Name, "exit") == 0)
    {
        printf("About     : It is used to terminate the project\n");
        printf("Usage     : exit\n");
    }
    else if(strcmp(Name, "ls") == 0)
    {
        printf("About     : It is used to list all files from current directory\n");
        printf("Usage     : ls\n");
    }
    else if(strcmp(Name, "clear") == 0)
    {
        printf("About     : It is used to clear the terminal\n");
        printf("Usage     : clear\n");
    }
    else if(strcmp(Name, "creat") == 0)
    {
        printf("About     : It is used to create new file\n");
        printf("Usage     : creat File_Name Permission\n");
        printf("File_Name : Name of file that we want to create\n");
        printf("Permission: Permission of new file\n");
        printf("Permission: Read -> 1\n Permission : Write -> 2\n Permission : Read + Write -> 3\n");
    }
    else if(strcmp(Name, "unlink") == 0)
    {
        printf("About     : It is used to delete existing file\n");
        printf("Usage     : unlink File_Name\n");
        printf("File_Name : Name of file that we want to delete\n");
    }
    else if(strcmp(Name, "stat") == 0)
    {
        printf("About     : It is used to get the complete information of the specific file\n");
        printf("Usage     : stat File_Name\n");
        printf("File_Name : Name of file whose information should be fetched\n");
    }
    else if(strcmp(Name,"open") == 0)
    {
        printf("About     : It is used to open the file\n");
        printf("Usage     : open File_Name Mode \n");
        printf("File_Name : Name of file which needs to be open\n");
        printf("Mode      : mode of file for which we are openning that file\n");         
    }
    else
    {
        printf("No manual entry found for %s\n",Name);
    }
}

////////////////////////////////////////////////////////////
//
//  Function Name : IsFileExist()
//  Description   : It is used to check whether the
//                  file is present or not
//  Input         : Name of File
//  Output        : True if Present / False if not present
//  Author        : Snehal Sawant
//  Date          : 01/08/2026
//
////////////////////////////////////////////////////////////

bool IsFileExist(
                    char name[]            //Name of file
                )
{
    PINODE temp = head;                    //Pointing to global varial of INODE
    bool bFlag = false;

    while(temp != NULL)
    {
        if(strcmp(temp->FileName, name) == 0)
        {
            bFlag = true;
            break;
        }
        temp = temp -> next;
    }
    return bFlag;
}

////////////////////////////////////////////////////////////
//
//  Function Name : CreateFile()
//  Description   : It is used to create the new file
//  Input         : Name of File, Permissions
//  Output        : File Descriptor
//  Author        : Snehal Sawant
//  Date          : 01/08/2026
//
//////////////////////////////////////////////////////

int CreateFile(
                char Name[],        //Name of file
                int permission      //File Permission
              )
{
    PINODE temp = head;
    int i = 0;

    if(superobj.FreeInodes == 0)
    {
        return ERR_NO_INODES;
    }

    //if permission value is wrong 
    //Permission = 1 -> READ 
    //Permission = 2 -> WRITE 
    //Permission = 3 -> READ + WRITE

    if(permission < 1 || permission > 3)
    {
        return ERR_INVALID_PARAMETER;
    }

    if(IsFileExist(Name) == true)           //Check if file already exist or not
    {
        return ERR_FILE_ALREADY_EXIST;
    }

    while(temp != NULL)                     //Search for empty inode from DILB
    {
        if(temp->FileType == 0)             //Chech if filetype is 0 then it is empty inode and we can use it to create new file
        {
            break;                          //breaks the while loop
        }
        temp = temp->next;
    }

    if(temp == NULL)                      //Rare case - if not found empty inode after whole list traversal
    {
        return ERR_NO_INODES;
    }

    for(i = 3; i < MAXINODE; i++)       // Search empty UFDT entry - We are starting from 3 because 0,1,2 are reserved for standard input, output and error
    {
        if(uareaobj.UFDT[i] == NULL)
        {
            break;
        }
    }

    if(i == MAXOPENFILES)            // Rare Case : inode available but UFDT entry not found then
    {
        return ERR_MAX_FILES_OPEN;
    }

    //Allocate memory for filetable
    uareaobj.UFDT[i] = (PFILETABLE)malloc(sizeof(FILETABLE));

    //Initialize FileTable
    uareaobj.UFDT[i]->ReadOffset = 0;
    uareaobj.UFDT[i]->WriteOffset = 0;
    uareaobj.UFDT[i]->Mode = permission;

    //Connect filetable with Inode
    uareaobj.UFDT[i]->ptrinode = temp;

    //Initialize FileName in Inode
    strcpy(uareaobj.UFDT[i]->ptrinode->FileName,Name); 

    //Initialize FileSize with MAXFILESIZE in Inode
    uareaobj.UFDT[i]->ptrinode->FileSize = MAXFILESIZE;

    //Initialize ActualFileSize with 0 in Inode, file is empty
    uareaobj.UFDT[i]->ptrinode->ActualFileSize = 0;

    //Initialize FileType with REGULARFILE in Inode
    uareaobj.UFDT[i]->ptrinode->FileType = REGULARFILE;

    //Initialize ReferenceCount with 1 in Inode - Because we are creating new file so reference count will be 1
    uareaobj.UFDT[i]->ptrinode->ReferenceCount = 1;

    //Initialize Permission given by user in Inode
    uareaobj.UFDT[i]->ptrinode->Permission = permission;

    //Allocate memory for files data - Actual Data Block
    uareaobj.UFDT[i]->ptrinode->Buffer = (char *)malloc(MAXFILESIZE);

    memset(uareaobj.UFDT[i]->ptrinode->Buffer, 0, MAXFILESIZE); //Initialize the buffer with 0

    superobj.FreeInodes--;

    return i;
}

///////////////////////////////////////////////////////////////////
//
//  Function Name : LsFile()
//  Description   : It is used to display names of all files 
//                  present in current directory
//  Input         : None
//  Output        : List of files present in current directory
//  Author        : Snehal Sawant
//  Date          : 01/08/2026
//
///////////////////////////////////////////////////////////////////

void LsFile()
{
    PINODE temp = head;

    printf("----------------------------------------------------------\n");
    printf("------------Marvellous CVFS Files Information-------------\n");
    printf("----------------------------------------------------------\n");

    while(temp != NULL)
    {
        if(temp->FileType != 0)
        {
            printf("%s\n",temp->FileName);
        }

        temp = temp->next;
    }
    printf("----------------------------------------------------------\n");
}

///////////////////////////////////////////////////////////////////
//
//  Function Name : LsFile_All()
//  Description   : It is used to display details of all
//                  files present in current directory
//  Input         : None
//  Output        : List of files present in current directory
//  Author        : Snehal Sawant
//  Date          : 02/08/2026
//
///////////////////////////////////////////////////////////////////

void LsFile_All()
{
    PINODE temp = head;

    printf("----------------------------------------------------------\n");
    printf("------------Marvellous CVFS Files Information-------------\n");
    printf("----------------------------------------------------------\n");

    printf("File Name   Inode Number    ActualFIleSize   Permission \n",temp->FileName, temp->InodeNumber, temp->ActualFileSize, temp->Permission);  // FileName,InodeNumber,ActualFileSize,Permission

    while(temp != NULL)
    {
        if(temp->FileType != 0)
        {
            printf("%s\t\t%d\t\t%d\t\t%d\n",temp->FileName, temp->InodeNumber, temp->ActualFileSize, temp->Permission);  // FileName,InodeNumber,ActualFileSize,Permission
        }
        temp = temp->next;
    }
}

////////////////////////////////////////////////////////////////
//
//  Function Name : stat_file()
//  Description   : It is used to display details of 
//                  specific file present in current directory
//  Input         : File Name
//  Output        : Exit status of function
//  Author        : Snehal Sawant
//  Date          : 02/08/2026
//
////////////////////////////////////////////////////////////////

int stat_file(
                char name[]             //Name of file
             )
{
    PINODE temp = NULL;
    int Permission = 0, Type = 0;

    if(IsFileExist(name) == false)
    {
        return ERR_FILE_NOT_EXIST;
    }

    temp = head;

    while(temp != NULL)
    {
        if(strcmp(temp->FileName, name) == 0)       // Comparing name of file with inode filename
        {
            printf("-----------------------------------------------------------\n");
            printf("------------ Statistical Information of File --------------\n");
            printf("-----------------------------------------------------------\n");
            printf("File Name :  %s\n",temp->FileName);
            printf("Inode Number : %d\n",temp->InodeNumber);
            printf("File Size : %d\n",temp->FileSize);
            printf("Actual File Size : %d\n",temp->ActualFileSize);
            printf("Reference Count : %d\n",temp->ReferenceCount);

            Permission = temp->Permission;
            if(Permission == READ)
            {
                printf("File Permission : Read Only\n");
            }
            else if(Permission == WRITE)
            {
                printf("File Permission : Write\n");
            }
            else if(Permission == READ + WRITE)
            {
                printf("File Permission : Read + Write\n");
            }

            Type = temp->FileType;

            if(Type == REGULARFILE)
            {
                printf("File Type : Regular File\n");
            }
            else if(Type == SPECIALFILE)
            {
                printf("File Type : Special File\n");
            }

            printf("----------------------------------------------------------\n");

            break;              //This breaks the foor loop
        }
        temp = temp->next;
    }
    return EXECUTE_SUCCESS;
}

/////////////////////////////////////////////////////////////
//
//  Function Name : unlink_file()
//  Description   : It is used to delete the specific file 
//                  present in current directory
//  Input         : File Name
//  Output        : Exit status of function
//  Author        : Snehal Sawant
//  Date          : 02/08/2026
//
/////////////////////////////////////////////////////////////

int unlink_file(
                    char name[]
               )
{
    PINODE temp = NULL;
    int i = 0;

    if(IsFileExist(name) == false)
    {
        return ERR_FILE_NOT_EXIST;
    }

    //Travel UFDT
    for(i = 3; i < MAXOPENFILES; i++)
    {
        if(uareaobj.UFDT[i] != NULL)
        {
            if(strcmp(uareaobj.UFDT[i]->ptrinode->FileName, name) == 0)
            {
                //Deallocate memory of Buffer
                free(uareaobj.UFDT[i]->ptrinode->Buffer);

                uareaobj.UFDT[i]->ptrinode->Buffer = NULL;   //  Make Buffer pointer NULL after deallocating memory else it will give segmentation fault while read

                strcpy(uareaobj.UFDT[i]->ptrinode->FileName, "\0");  //  Make FileName empty

                uareaobj.UFDT[i]->ptrinode->FileSize = 0;     //  Make FileSize 0

                uareaobj.UFDT[i]->ptrinode->ActualFileSize = 0;     //  Make ActualFileSize 0

                uareaobj.UFDT[i]->ptrinode->FileType = 0;     //  Make FileType 0 

                uareaobj.UFDT[i]->ptrinode->Permission = 0;     //  Make Permission 0

                uareaobj.UFDT[i]->ptrinode->ReferenceCount = 0;     //  Make ReferenceCount 0

                //Do not set Inode number to 0, we will need it for new file
                //Deallocate memory of FileTable

                free(uareaobj.UFDT[i]);

                uareaobj.UFDT[i] = NULL;   //  Make UFDT entry NULL after deallocating memory

                superobj.FreeInodes++;     //  Increase FreeInodes in SuperBlock

                printf("Marvellous CVFS : File %s gets deleted successfully\n",name);

                break;      //  We got the file in UFDT so break the loop - IMP
            }
        }//End of if(uareaobj.UFDT[i] != NULL)
    }//End of for loop

    return EXECUTE_SUCCESS;
    
}//End of unlink_file function

///////////////////////////////////////////////////////////////////
//
//  Function Name : write_file()
//  Description   : It is used to write data to the specific file 
//                  present in current directory
//
//  Input         : File Descriptor, 
//                  Buffer(Data that we want to write), 
//                  Size of data to write
//
//  Output        : Number of bytes successfully written to the file
//  Author        : Snehal Sawant
//  Date          : 02/08/2026
//
/////////////////////////////////////////////////////////////////////

int write_file(
                int fd,             //File descriptor
                char *data,         //Buffer(Data that we want to write)
                int size            //Size of data to write
              )
{
    int offset = 0;

    //If fd is invalid or greater than MAXOPENFILES then return error
    if(fd < 0 || fd > MAXOPENFILES)
    {
        return ERR_INVALID_PARAMETER;
    }

    //If permission is set to READ i.e 1 so it should return error
    if(uareaobj.UFDT[fd]->ptrinode->Permission < WRITE)
    {
        return ERR_PERMISSION_DENIED;
    }

    // Check if space is there in Buffer or not
    if((MAXFILESIZE - uareaobj.UFDT[fd]->WriteOffset) < size)
    {
        return ERR_INSUFFICIENT_SPACE;
    }

    //Actual writing of data into file
    strncpy((uareaobj.UFDT[fd]->ptrinode->Buffer + uareaobj.UFDT[fd]->WriteOffset),data,size);

    //Update the write offset
    uareaobj.UFDT[fd]->WriteOffset = uareaobj.UFDT[fd]->WriteOffset + size;

    //Update the write offset Actual file size
    uareaobj.UFDT[fd]->ptrinode->ActualFileSize = uareaobj.UFDT[fd]->ptrinode->ActualFileSize + size;
    
    return size;
}

//////////////////////////////////////////////////////////////////////
//
//  Function Name : read_file()
//  Description   : It is used to read data from the specific file 
//                  present in current directory
//
//  Input         : File Descriptor, 
//                  Address of Empty Buffer(Data that we want to read), 
//                  Size of data to read
//
//  Output        : Number of bytes successfully read from the file
//  Author        : Snehal Sawant
//  Date          : 02/08/2026
//
/////////////////////////////////////////////////////////////////////

int read_file(
                int fd,             //File descriptor
                char *data,         //Empty Buffer(Data that we want to read)
                int size            //Size of data to read
             )
{
    
    //If fd is invalid or greater than MAXOPENFILES then return error
    if(fd < 0 || fd > MAXOPENFILES)
    {
        return ERR_INVALID_PARAMETER;
    }

    //If size is invalid or less than 0
    if(size < 0)
    {
        return ERR_INVALID_PARAMETER;
    }

    //Check if file exists or not
    if(uareaobj.UFDT[fd] == NULL)
    {
        return ERR_FILE_NOT_EXIST;
    }
    
    //Check permission
    if(uareaobj.UFDT[fd]->ptrinode->Permission < READ)
    {
        return ERR_PERMISSION_DENIED;
    }

    //Insufficient Data
    if(uareaobj.UFDT[fd]->ReadOffset >= uareaobj.UFDT[fd]->ptrinode->ActualFileSize)
    {
        return ERR_INSUFFICIENT_DATA;
    }

    // Update size if the remaining data to be read is less than size given by user
    if((uareaobj.UFDT[fd]->ptrinode->ActualFileSize - uareaobj.UFDT[fd]->ReadOffset) < size)
    {        
        size = uareaobj.UFDT[fd]->ptrinode->ActualFileSize - uareaobj.UFDT[fd]->ReadOffset;    
    }  

    //Actual reading of data from file
    strncpy(data,uareaobj.UFDT[fd]->ptrinode->Buffer + uareaobj.UFDT[fd]->ReadOffset,size);

    data[size] = '\0';
    
    //Update the read offset
    uareaobj.UFDT[fd]->ReadOffset = uareaobj.UFDT[fd]->ReadOffset + size;

    //This resets the readoffset to 0 when file reading is done it will start reading from first letter
    // if(uareaobj.UFDT[fd]->ReadOffset > uareaobj.UFDT[fd]->ptrinode->ActualFileSize)
    // {
    //     uareaobj.UFDT[fd]->ReadOffset = 0;
    // }
    
    return size;
}

///////////////////////////////////////////////////////////////
//
//  Function Name : open_file()
//  Description   : It is used to open the specific file 
//                  present in current directory
//
//  Input:        : File Name,
//                  Mode of file
//
//  Output        : Exit status of function
//  Author        : Snehal Sawant
//  Date          : 04/08/2026
//
///////////////////////////////////////////////////////////////


int open_file(
                char Name[],            //File Name
                char *data,              //Empty Buffer(Data that we want to read)
                int permission 
            )
{
    int i = 0;
    PINODE temp = head;
    
    if(Name == NULL || permission <= 0 || permission > 3)
    {
        return ERR_INVALID_PARAMETER;
    }  

    //Search file name in inode
    while(temp != NULL)
    {
        if((strcmp(Name,temp->FileName) == 0) && (temp->FileType != 0))
        {
            break;
        }
        temp = temp->next;
    }

    //File exist or not
    if(temp == NULL)
    {
        return ERR_FILE_NOT_EXIST;
    }
    
    if(temp->Permission < permission)
    {
        return ERR_PERMISSION_DENIED;
    }

    //Actual reading of data from file
    if (temp->ActualFileSize > 0)
    {
        strcpy(data,temp->Buffer);
    }
    else
    {
        return ERR_INSUFFICIENT_DATA;
    }
    
    //Search for the NULL UFDT so the opened file fd will be set there
    for(i = 3; i < MAXOPENFILES; i++)
    {
        if(uareaobj.UFDT[i] == NULL)
        {
            break;
        }
    }

    //If i reaches till MAXOPENFILES number through the above for loop below condition becomes true
    if(i == MAXOPENFILES)
    {
        return ERR_MAX_FILES_OPEN;
    }
    uareaobj.UFDT[i] = (PFILETABLE)malloc(sizeof(FILETABLE));
    uareaobj.UFDT[i]->Mode = permission;
    uareaobj.UFDT[i]->ReadOffset = 0;
    uareaobj.UFDT[i]->WriteOffset = 0;
    uareaobj.UFDT[i]->ptrinode = temp;

    temp->ReferenceCount++;

    return i;
}

/////////////////////////////////////////////////////////////////////////////////////////////
//
//  Function Name       : close_file()
//  Description         : It is used to close the specific file
//
//  Input               : File Name                     
//  Output              : Open
//         
//  Author              : Snehal Sawant
//  Date                : 5/08/2026
//
/////////////////////////////////////////////////////////////////////////////////////////////

int close_file(int fd)
{
    if(fd < 0 || fd >= MAXOPENFILES)
    {
        return ERR_INVALID_PARAMETER;
    }

    // If file not open
    if(uareaobj.UFDT[fd] == NULL)
    {
        return ERR_FILE_NOT_OPEN; 
    }

    //if file is opened
    uareaobj.UFDT[fd]->ptrinode->ReferenceCount--;

    free(uareaobj.UFDT[fd]);                // free the FD from file table

    uareaobj.UFDT[fd] = NULL;

    return EXECUTE_SUCCESS;
}

/////////////////////////////////////////////////////////////////////////////////////////////
//
//  Function Name :     Backup_File()
//  Description :       It is used to Backup the content of specific file into HDD
//
//  Input:              File Name                     
//  Output:             Backup of all files created in this project is stored in HDD    
//     
//  Author :            Snehal Sawant
//  Date :              5/08/2026
//
/////////////////////////////////////////////////////////////////////////////////////////////


void Backup_File()
{   
    PINODE temp = head;
    char FullPath[260];
    int fd = 0; 

    while(temp != NULL)
    {
        if(temp->FileType != 0)
        {
            sprintf(FullPath,"%s%s",BACKUP_PATH, temp->FileName);            
                            //C:\\Users\\SAI\\Desktop\\LB\\CVFS\\Backup\\temp->FileName  

            fd = creat(FullPath,0777);  
           
            write(fd, temp->Buffer,temp->ActualFileSize);
        }        

        temp = temp->next;
    }

}

///////////////////////////////////////////////////////////////////
//
//  Entry Point function of the CVFS project
//
///////////////////////////////////////////////////////////////////

int main()
{
    //Input command from user
    char str[80] = {'\0'};

    //Tokenized command from user
    char Command[5][20] = {{'\0'}};     //Bcoz of 2D array we are using double curly brackets

    //Input buffer to write data into file
    char InputBuffer[MAXFILESIZE] = {'\0'};

    //Empty Buffer to read data from file
    char *EmptyBuffer = NULL;

    int iCount = 0, iRet = 0, size = 0;
    
    StartAuxillaryDataInitialisation();

    printf("----------------------------------------------------------\n");
    printf("-----------Marvellous CVFS Started Successfully-----------\n");
    printf("----------------------------------------------------------\n");
    
    //Infinite Listening Shell      --  Its using infinite while loop until user enters exit keyword
    while(1)
    {
        fflush(stdin);

        strcpy(str,"");

        printf("\nMarvellous CVFS : > ");
        fgets(str,sizeof(str),stdin);  //(where, how much, from where)

        iCount = sscanf(str,"%s %s %s %s %s",Command[0],Command[1],Command[2],Command[3],Command[4]); 
               //(from where, how much, where to store)

        fflush(stdin);

        if(iCount == 1)
        {
            //Marvellous CVFS : > exit
            if(strcmp(Command[0],"exit") == 0)
            {
                Backup_File();
                printf("Thank you for using Marvellous CVFS\n");
                printf("Deallocating all resources of Marvellous CVFS\n");

                break;
            }
            //Marvellous CVFS : > help
            else if(strcmp(Command[0],"help") == 0)
            {
                DisplayHelp();
            }
            //Marvellous CVFS : > clear
            else if(strcmp(Command[0],"clear") == 0)
            {
                #ifdef _WIN32
                    system("cls");
                #else
                    system("clear");
                #endif
            }

            //Marvellous CVFS : > ls
            else if(strcmp(Command[0],"ls") == 0)
            {
                LsFile();
            }
            else
            {
                printf("Command not found\n");
                printf("Please refer help opiton to get more information\n");
                printf("Please refer manual page of command using man\n");
            }
        }
        else if(iCount == 2)
        {
            //  Marvellous CVFS : > man open
            if(strcmp(Command[0],"man") == 0)
            {
                ManPageDisplay(Command[1]);
            }
            //  Marvellous CVFS : > ls -a
            else if((strcmp(Command[0],"ls") == 0) && (strcmp(Command[1],"-a") == 0))
            {
                LsFile_All();
            }
            //  Marvellous CVFS : > stat Ganesh.txt
            else if(strcmp(Command[0],"stat") == 0)
            {
                iRet = stat_file(Command[1]);
                if (iRet == ERR_FILE_NOT_EXIST)
                {
                    printf("Error : File not exist\n");
                    printf("Please use ls command to check names of all files\n");
                }
            }
            //  Marvellous CVFS : > unlink Ganesh.txt
            else if(strcmp(Command[0],"unlink") == 0)
            {
                iRet = unlink_file(Command[1]);
                if (iRet == ERR_FILE_NOT_EXIST)
                {
                    printf("Error : File not exist\n");
                    printf("Please use ls command to check names of all files\n");
                }
            }
           
            //  Marvellous CVFS : > write 3
            else if(strcmp(Command[0],"write") == 0)
            {
                printf("Enter the data that you want to write in file : \n");
                
                fgets(InputBuffer,MAXFILESIZE,stdin);

                InputBuffer[strcspn(InputBuffer, "\n")] = '\0';
                
                size = strlen(InputBuffer);
                
                iRet = write_file(atoi(Command[1]), InputBuffer, size);

                if (iRet == ERR_INVALID_PARAMETER)
                {
                    printf("Error : Invalid parameters\n");
                    printf("Please use man page to get actual parameters\n");
                }
                else if (iRet == ERR_PERMISSION_DENIED)
                {
                    printf("Error : There is no permission to write the data\n");
                }
                else if (iRet == ERR_INSUFFICIENT_SPACE)
                {
                    printf("Error : Insufficient space in file\n");
                }
                else
                {
                    printf("%d bytes of data is written successfully to the file\n",iRet);
                }
            }

            //Marvellous CVFS : > close 3   // here 3 is fd
            else if(strcmp(Command[0],"close") == 0)
            {               

                iRet = close_file(atoi(Command[1]));

                if(iRet == ERR_INVALID_PARAMETER)
                {
                    printf("Error : Invalid Parameter\n");
                    printf("Please refer manpage for more information\n");
                }

                else if(iRet == EXECUTE_SUCCESS)
                {
                    printf("File closed successfully\n");
                }   
                else
                {
                    printf("Error....");
                }                                   
                                
            } // End of close
            else
            {
                printf("Command not found\n");
                printf("Please refer help opiton to get more information\n");
                printf("Please refer manual page of command using man\n");
            }
        }
        else if(iCount == 3)
        {
            //Marvellous CVFS : > creat Demo.txt 3 -- It takes 3 words as a command so it comes in iCount == 3
            if(strcmp(Command[0], "creat") == 0)
            {
                iRet = CreateFile(Command[1], atoi(Command[2])); //Convert string to integer 
                                              //atoi = ascii to integer

                if(iRet == ERR_NO_INODES)
                {
                    printf("Error : Unable to create new file\n");
                    printf("Because there is no free inode\n");
                }
                else if(iRet == ERR_INVALID_PARAMETER)
                {
                    printf("Error : Unable to create new file\n");
                    printf("Because parameters of command are invalid\n");
                    printf("Please use man page to get actual parameters\n");
                }
                else if(iRet == ERR_FILE_ALREADY_EXIST)
                {
                    printf("Error : Unable to create new file\n");
                    printf("Because the file name is already present\n");
                    printf("Please use ls command to check names of all files\n");
                }
                else if(iRet == ERR_MAX_FILES_OPEN)
                {
                    printf("Error : Unable to create new file\n");
                    printf("Because the UFDT is full\n");
                    printf("Please close some files and try again\n");
                }
                else
                {
                    printf("File Succcessfully created with FD : %d\n",iRet);
                }
            }
            //Marvellous CVFS : > read  3 10 -- It takes 3 words as a command so it comes in iCount == 3
            else if(strcmp(Command[0], "read") == 0)
            {
                EmptyBuffer = (char *)malloc(atoi(Command[2]));

                iRet = read_file(atoi(Command[1]),EmptyBuffer,atoi(Command[2]));

                if (iRet == ERR_INVALID_PARAMETER)
                {
                    printf("Error : Invalid parameters\n");
                    printf("Please use man page to get actual parameters\n");
                }
                else if (iRet == ERR_FILE_NOT_EXIST)
                {
                    printf("Error : File not exist\n");
                }
                else if (iRet == ERR_INSUFFICIENT_DATA)
                {
                    printf("Error : Insufficient data\n");
                }
                else if (iRet == ERR_PERMISSION_DENIED)
                {
                    printf("Error : Permission Denied\n");
                }
                else
                {
                    printf("Read operation is successfully\n",iRet);

                    printf("Data from file is : \n");
                    printf("%s\n",EmptyBuffer);
                }
            }

            // Marvellous CVFS : > open Demo.txt 3   //  here 3 is mode
            else if(strcmp(Command[0], "open") == 0)
            {
                EmptyBuffer = (char *)malloc(MAXFILESIZE);

                iRet = open_file(Command[1],EmptyBuffer,atoi(Command[2]));

                if (iRet == ERR_INVALID_PARAMETER)
                {
                    printf("Error : Invalid parameters\n");
                    printf("Please use man page to get actual parameters\n");
                }
                else if (iRet == ERR_FILE_NOT_EXIST)
                {
                    printf("Error : File not exist\n");
                }
                else if (iRet == ERR_INSUFFICIENT_DATA)
                {
                    printf("Error : Insufficient data\n");
                }
                else if (iRet == ERR_PERMISSION_DENIED)
                {
                    printf("Error : Permission Denied\n");
                }
                 else if(iRet == ERR_MAX_FILES_OPEN)
                {
                    printf("Error : Maximum files opened currently\n");
                }
                else
                {
                   printf("File opened successfully\n");
                   printf("File Descriptor : %d\n",iRet);

                    printf("Data from file is : \n");
                    printf("%s\n",EmptyBuffer);
                }
            }
            else
            {
                printf("Command not found\n");
                printf("Please refer help opiton to get more information\n");
                printf("Please refer manual page of command using man\n");
            }
        }
        else if(iCount == 4)
        {
           
        }
        else
        {
            printf("Command not found\n");
            printf("Please refer help opiton to get more information\n");
            printf("Please refer manual page of command using man\n");
        }
    }//End of while

    return 0;
}//End of main
