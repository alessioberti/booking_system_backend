from sqlalchemy_schemadisplay import create_schema_graph
from sqlalchemy import MetaData
from app.extensions import db
from app import create_app

def main():
        app = create_app()
        metadata = db.metadata

        with app.app_context():
        
            graph = create_schema_graph(
                metadata=metadata,
                show_datatypes=False,
                show_indexes=False,
                rankdir='LR',
                concentrate=False
            )
    
            graph.write_png('schema_diagram.png')
            print("Diagramma salvato come schema_diagram.png")

if __name__ == "__main__":
    main()