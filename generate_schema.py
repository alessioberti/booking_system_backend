from sqlalchemy_schemadisplay import create_schema_graph
from sqlalchemy import MetaData
from app.extensions import db
from app import create_app

FILE_NAME = "schema_diagram.png"

def main():
        app = create_app()
        metadata = db.metadata

        with app.app_context():
        
            graph = create_schema_graph(
                metadata=metadata,
                show_datatypes=True,
                show_indexes=False,
                rankdir='LR',
                concentrate=False,
                engine=db.engine
            )
    
            graph.write_png(FILE_NAME)
            print("Generated", FILE_NAME)

if __name__ == "__main__":
    main()
