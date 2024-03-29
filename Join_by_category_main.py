#region import
import clr
clr.AddReference('RevitAPI')
import Autodesk
from Autodesk.Revit.DB import GeometryInstance, FilteredElementCollector, JoinGeometryUtils, Options, ElementId, ElementIntersectsSolidFilter, BuiltInParameter
clr.AddReference('RevitServices')
import RevitServices
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager
clr.AddReference('System')
from System.Collections.Generic import List
from System import Math, DateTime, Double, TimeSpan
from System.Diagnostics import Process, Stopwatch
#endregion
#region классы и общие функции
class TimeCounter:
	def __init__(self):
		#self.name = name
		self.time = Stopwatch.StartNew()
		self.time.Start()
	def stop(self):
		self.time.Stop()
		return self.time.Elapsed
def flatten_List(a, res=None):
	if res is None:
		res = []
	[flatten_List(i, res) if isinstance(a, list) else res.append(i) for i in a]
	return res
#endregion
#region сбор элементов для объединения
def fcollector_by_cat_to_id(doc,c_id):
	return FilteredElementCollector(doc).OfCategoryId(c_id).WhereElementIsNotElementType().ToElements()
doc = DocumentManager.Instance.CurrentDBDocument
cats = doc.Settings.Categories
#collector = FilteredElementCollector(doc)
cats_string = UnwrapElement(IN[0])
cats_ids_names = [(cat.Id, cat.Name) for cat in cats if cat.Name in cats_string]
parts = []
elements = []
[parts.append(fcollector_by_cat_to_id(doc,id_name[0])) if id_name[1] == "Части" else elements.append(fcollector_by_cat_to_id(doc,id_name[0])) for id_name in cats_ids_names]
#endregion
#region main
time = TimeCounter()
if IN[1]:
	results = 0
	#region функции для объединения
	def join(x,y):
		try:
			JoinGeometryUtils.JoinGeometry(doc,x,y)
			results = 1
		except:
			results = 0
		return results
	def join_s(x,y):
		try:
			JoinGeometryUtils.JoinGeometry(doc,x,y)
			JoinGeometryUtils.SwitchJoinOrder(doc,x,y)
			results = 1
		except:
			results = 0
		return results
	def get_geometys(element):
		if element.get_Geometry(geo_options):
			for geometry_inst in element.get_Geometry(geo_options):
				if geometry_inst.GetType() == Autodesk.Revit.DB.GeometryInstance:
					for geometry in geometry_inst.SymbolGeometry:
						if geometry.GetType() == Autodesk.Revit.DB.Solid and Math.Round(geometry.Volume,3) != 0:
							return geometry
				else:
					if geometry_inst.GetType() == Autodesk.Revit.DB.Solid and Math.Round(geometry_inst.Volume,3) != 0:
						return geometry_inst
	#endregion
	#region параметры для объединения
	opt = Options()
	items1 = flatten_List(elements)
	catIdlist = [id_name[0] for id_name in cats_ids_names]
	ids = [i.Id for i in items1]
	i_list_ids = List[ElementId](ids)
	inter = []
	aliter = []
	alliter = []
	geo_options = Options()
	geo_options.ComputeReferences = False
	geo_options.IncludeNonVisibleObjects = False	
	# for i in items1:
	# 	ids.append(i.Id)
	#endregion
	#region main итерации, что-то можно заменить на генераторы списков для 
	TransactionManager.Instance.EnsureInTransaction(doc)
	for i1 in items1:	
		geomSolid = get_geometys(i1)
		if geomSolid != None:
			for ost in catIdlist:
				elems = FilteredElementCollector(doc,i_list_ids).OfCategoryId(ost).WhereElementIsNotElementType()
				elems_solid_filter = []
				elems_solid_filter.append(elems.WherePasses(ElementIntersectsSolidFilter(geomSolid)).ToElements())
				els_sol_fil_flat = flatten_List(elems_solid_filter)
				for els in els_sol_fil_flat:
					if els.Id.ToString() == i1.Id.ToString():
						pass
					else:
						if JoinGeometryUtils.AreElementsJoined(doc,els,i1):
							pass
						else:
							results += join(els,i1)
	TransactionManager.Instance.ForceCloseTransaction()
	#endregion
else:
	results = 0
	#region разделение геометрии
	items1 = flatten_List(elements)
	TransactionManager.Instance.EnsureInTransaction(doc)
	for i in items1:
		test = JoinGeometryUtils.GetJoinedElements(doc, i)
		if test:
			for t in test:
				JoinGeometryUtils.UnjoinGeometry(doc,i,doc.GetElement(t))
				results += 1
	TransactionManager.Instance.ForceCloseTransaction()
	#endregion
#endregion
t = time.stop()
if IN[1]:
	OUT = "Join elements = " + str(results), "Minutes, Seconds, Milliseconds = ", [t.Minutes, t.Seconds, t.Milliseconds]
else:
	OUT = "Unjoin elements = " + str(results), "Minutes, Seconds, Milliseconds = ", [t.Minutes, t.Seconds, t.Milliseconds]
