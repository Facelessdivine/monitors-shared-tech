# monitors-shared-tech

This is a project for verify the status of the services of the monitors in shared tech, and additionally has a service of mail sender to notify the user whenever a service is not in optimal status

# Clone the repo

    Git clone <http url>

    cd monitors-shared-tech

# activate the virtual environment

    py -m venv myenv
    
    myenv\Scripts\activate.bat

# Install the project dependences

    pip install -r requirements.txt

# Install the project dependences

    py monitor_watcher.py

And there you go


## Project diagram
```mermaid
graph  TD

A[Python service start]  -->  B(Verify monitors)

B  -->  C{Is something wrong}

C  -->  D[Keep]

C  -->  E[Everyting okay]

E  -- Retry again in one minute -->  B

D  -->  F[Send mail of the failing services]

F  -->  B

F  -->  H[Read mail and send it to Teams chat]

H  -->  G[Create adaptive card]

G  -->  I[Terminate service]

```