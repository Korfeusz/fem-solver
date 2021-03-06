import fenics
from constitutive_relations import ConstitutiveRelation
from generalized_alpha_parameters import GeneralizedAlphaParameters
from .problem_form import ProblemForm
from fields.fields import Fields
from typing import Callable

class ElastodynamicsForm(ProblemForm):
    def __init__(self, mass_density: float,
                 eta_m: fenics.Constant,
                 eta_k: fenics.Constant,
                 constitutive_relation: ConstitutiveRelation,
                 generalized_alpha_parameters: GeneralizedAlphaParameters,
                 delta_t: fenics.Constant,
                 f_ext: Callable[[fenics.Function], fenics.Expression]):
        self.rho = fenics.Constant(mass_density)
        self.eta_m = eta_m
        self.eta_k = eta_k
        self.constitutive_relation = constitutive_relation
        self.gamma = generalized_alpha_parameters.gamma
        self.beta = generalized_alpha_parameters.beta
        self.alpha_f = generalized_alpha_parameters.alpha_f
        self.alpha_m = generalized_alpha_parameters.alpha_m
        self.delta_t = delta_t
        self.f_ext = f_ext

    @property
    def c_1(self) -> fenics.Expression:
        return self.gamma * (1 - self.alpha_f) / (self.beta * self.delta_t)

    @property
    def c_2(self) -> fenics.Expression:
        return 1 - self.gamma/self.beta * (1 - self.alpha_f)

    @property
    def c_3(self) -> fenics.Expression:
        return self.delta_t * (1 - self.alpha_f) * (1 - (self.gamma / (2 * self.beta)))

    @property
    def m_1(self) -> fenics.Expression:
        return  (1 - self.alpha_m) / (self.delta_t*self.delta_t * self.beta)

    @property
    def m_2(self) -> fenics.Expression:
        return  (1 - self.alpha_m) / (self.delta_t * self.beta)

    @property
    def m_3(self) -> fenics.Expression:
        return  1 - (1 - self.alpha_m) / (2 * self.beta)


    def m(self, u: fenics.Function, w: fenics.Function) -> fenics.Expression:
        return self.rho*fenics.inner(u, w)*fenics.dx

    def c(self, u: fenics.Function, w: fenics.Function,
          constitutive_relation_function: Callable[[fenics.Function], fenics.Expression]) -> fenics.Expression:
        return self.eta_m * self.m(u, w) + self.eta_k * self.k(u, w, constitutive_relation_function)

    def k(self, u: fenics.Function, w: fenics.Function,
          constitutive_relation_function: Callable[[fenics.Function], fenics.Expression]) -> fenics.Expression:
        return fenics.inner(constitutive_relation_function(u), fenics.sym(fenics.grad(w))) * fenics.dx


    def get_weak_form_lhs(self, fields: Fields) -> fenics.Expression:
        u = fields.u
        w = fields.w
        return (1 - self.alpha_f) * self.k(u, w, self.constitutive_relation.get_new_value) \
               + self.c_1 * self.c(u, w, self.constitutive_relation.get_new_value) + self.m_1 * self.m(u, w)

    def get_weak_form_rhs(self, fields: Fields) -> fenics.Expression:
        u = fields.u_old
        v = fields.v_old
        a = fields.a_old
        w = fields.w
        old_relation = self.constitutive_relation.get_old_value
        return -self.alpha_f * self.k(u, w, old_relation) + self.f_ext(w) \
               + self.c_1 * self.c(u, w, old_relation) - self.c_2 * self.c(v, w, old_relation)\
               - self.c_3 * self.c(a, w, old_relation)\
               + self.m_1 * self.m(u, w) + self.m_2 * self.m(v, w) - self.m_3 * self.m(a, w)

    # def get_weak_form_lhs(self, fields: Fields) -> fenics.Expression:
    #     u = fields.u
    #     w = fields.w
    #     return fenics.inner(self.constitutive_relation.get_new_value(u), fenics.sym(fenics.grad(w))) * fenics.dx
    #
    # def get_weak_form_rhs(self, fields: Fields) -> fenics.Expression:
    #     # u = fields.u_old
    #     # v = fields.v_old
    #     # a = fields.a_old
    #     w = fields.w
    #     # old_relation = self.constitutive_relation.get_old_value
    #     return  self.f_ext(w)