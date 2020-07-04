import fenics
from problem_definition import  TimeStepBuilder
from fem_solver import get_fem_solver
from .simulation_parameters import SimulationParameters

class Simulation:
    def __init__(self, simulation_parameters: SimulationParameters):
        self.mesh_creator = simulation_parameters.mesh_creator
        self.spaces = simulation_parameters.spaces
        self.boundary_markers = simulation_parameters.boundary_markers
        self.bc_creator = simulation_parameters.bc_creator
        self.boundary_excitation = simulation_parameters.boundary_excitation
        self.fields = simulation_parameters.fields
        self.field_updates = simulation_parameters.field_updates
        self.fem_solver_type = simulation_parameters.fem_solver_type
        self.problem = simulation_parameters.problem
        self.alpha_params = simulation_parameters.alpha_params
        self.time_params = simulation_parameters.time_params
        self.time_step_builder = TimeStepBuilder(time_step_type=simulation_parameters.time_step_type)
        self.xdmf_file = fenics.XDMFFile(simulation_parameters.save_file_name)
        self.xdmf_file.parameters["flush_output"] = True
        self.xdmf_file.parameters["functions_share_mesh"] = True
        self.xdmf_file.parameters["rewrite_function_mesh"] = False

    def run(self):
        mesh = self.mesh_creator.get_mesh()
        self.spaces.generate(mesh=mesh)
        self.boundary_markers.mark_boundaries(mesh=mesh)
        bc = self.bc_creator.apply(vector_space=self.spaces.vector_space, boundary_markers=self.boundary_markers.value)
        ds = fenics.Measure('ds', domain=mesh, subdomain_data=self.boundary_markers.value)
        self.boundary_excitation.set_ds(ds=ds)
        self.fields.generate(spaces=self.spaces)
        fem_solver = get_fem_solver(fem_solver=self.fem_solver_type, problem=self.problem, fields=self.fields,
                                    boundary_conditions=bc)
        self.time_step_builder.set(alpha_params=self.alpha_params, time_params=self.time_params, fem_solver=fem_solver,
                              file=self.xdmf_file, boundary_excitation=self.boundary_excitation,
                              field_updates=self.field_updates, fields=self.fields)
        time_step = self.time_step_builder.build()

        for (i, t) in enumerate(self.time_params.linear_time_space[1:]):
            print("Time: ", t)
            time_step.run(i)